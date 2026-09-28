`timescale 1ns/1ps
module tb_field_sync;
    localparam N=32;
    parameter integer FIELD_LINES=625;
    reg clk=0,reset=1,field_start=0,out_sol=0;
    wire vs_n,frame_start;
    integer t,starts=0,low_cycles=0;
    field_sync #(.H_SAMPLES(N),.VS_LINES(5)) dut(clk,reset,field_start,out_sol,vs_n,frame_start);
    always #5 clk=!clk;
    initial begin
        @(posedge clk); #1; @(negedge clk); reset=0;
        // Odd FIELD_LINES alternates whole/half input-line phase; even does not.
        for(t=0;t<(2*FIELD_LINES+20)*N;t=t+1) begin
            field_start=(t==0 || t==FIELD_LINES*N);
            out_sol=(t%N==0);
            @(posedge clk); #1;
            if(frame_start) begin
                starts=starts+1;
                if(t!=2*N && t!=(FIELD_LINES+2)*N) $fatal(1,"field start phase wrong t=%0d",t);
            end
            if(!vs_n) low_cycles=low_cycles+1;
            if(!vs_n && !((t>=2*N && t<7*N)||(t>=(FIELD_LINES+2)*N && t<(FIELD_LINES+7)*N)))
                $fatal(1,"VS width or phase wrong t=%0d",t);
            @(negedge clk);
        end
        if(starts!=2 || low_cycles!=10*N) $fatal(1,"field count/VS width wrong");
        $display("PASS field_sync: field period=%0d output lines, 2 frames, five-line VS",FIELD_LINES);
        $finish;
    end
endmodule
