`timescale 1ns/1ps
module tb_video_core;
    parameter integer N=32, FIELD_LINES=625;
    reg clk=0,reset=1,sample_ce=0,line_start=0,field_start=0;
    reg [23:0] pixel_in=0;
    wire [23:0] rgb;
    wire blank_n,hs_n,vs_n,out_sol,frame_start,protocol_error;
    wire [$clog2(N)-1:0] out_x;
    wire [11:0] out_y;
    video_core #(.H_SAMPLES(N),.HS_WIDTH(4),.X_START(6),.X_END(N-4),
                 .Y_START(8),.Y_END(FIELD_LINES-8)) dut(.*);
    always #5 clk=~clk;
    function [23:0] pattern(input integer row,input integer x);
        pattern=((row*24'h319b7)^(x*24'h10213))&24'hffffff;
    endfunction
    task step(input integer t,input integer fields_enabled);
      begin
        sample_ce=(t%2==0);line_start=(t%(2*N)==0);
        field_start=fields_enabled && t%(N*FIELD_LINES)==0;
        pixel_in=pattern(t/(2*N),(t%(2*N))/2);
        @(posedge clk);#1;
      end
    endtask
    integer t,x,y,row,delta,checks=0,frames=0;
    reg active;
    reg [23:0] expected;
    initial begin
      @(posedge clk);#1;@(negedge clk);reset=0;
      for(t=0;t<6*N*FIELD_LINES;t=t+1) begin
        step(t,1);
        if(protocol_error) $fatal(1,"Unexpected protocol error t=%0d",t);
        if(t>=2*N+2) begin
          delta=t-(2*N+2);x=delta%N;y=(delta/N)%FIELD_LINES;row=(t-2)/(2*N)-1;
          active=x>=6 && x<N-4 && y>=8 && y<FIELD_LINES-8;
          expected=active?pattern(row,x):24'b0;
          if(out_x!==x || out_y!==y || blank_n!==active || rgb!==expected ||
             hs_n!==(x>=4) || vs_n!==(y>=5) || out_sol!==(x==0) ||
             frame_start!==(delta%(N*FIELD_LINES)==0))
            $fatal(1,"Alignment mismatch t=%0d x=%0d/%0d y=%0d/%0d rgb=%h/%h HS=%b VS=%b frame=%b",t,out_x,x,out_y,y,rgb,expected,hs_n,vs_n,frame_start);
          checks=checks+1;if(frame_start) frames=frames+1;
        end else if(blank_n || rgb!==0 || frame_start) $fatal(1,"Startup exposed pixels");
        @(negedge clk);
      end
      // Missing the next input line must blank the delayed RGB immediately.
      sample_ce=1;line_start=0;field_start=0;@(posedge clk);#1;
      if(!protocol_error || blank_n || rgb!==0) $fatal(1,"Fault did not blank RGB");
      @(negedge clk);reset=1;@(posedge clk);#1;
      if(blank_n || protocol_error) $fatal(1,"Reset did not clear pipeline");
      @(negedge clk);reset=0;
      for(t=0;t<24*N;t=t+1) begin
        step(t,t==0);
        if(protocol_error) $fatal(1,"Restart failed");
        @(negedge clk);
      end
      if(N==32) begin
        // Preserve input lines but remove all later fields, past Y saturation.
        for(t=24*N;t<4200*N;t=t+1) begin
          step(t,0);
          if(t>(FIELD_LINES+2)*N && (blank_n || rgb!==0)) $fatal(1,"Missing fields repeated old active window");
          @(negedge clk);
        end
        if(out_y!==12'hfff) $fatal(1,"Vertical counter did not saturate");
      end
      $display("PASS video_core N=%0d FIELD_LINES=%0d: %0d aligned RGB/HS/VS checks, %0d frame starts; blanking, sync loss, restart",N,FIELD_LINES,checks,frames);
      $finish;
    end
endmodule
