`timescale 1ns/1ps
module tb_stream_input_video;
    localparam N=32,FL=625;
    reg clk=0,reset=1,sample_ce=0,hs_n_sampled=1,vs_n_async=1,no_hs=0,no_vs=0;
    reg [23:0] rgb_sampled=0;
    wire [23:0] rgb;
    wire blank_n,hs_n,vs_n,sync_valid,protocol_error;
    wire [2:0] fault_history;
    integer t=0,checked=0,source_line,source_x;
    reg [23:0] expected;
    always #5 clk=~clk;
    stream_input_video #(.H_SAMPLES(N),.VS_ALIGN_CYCLES(7),.HS_WIDTH(4),
      .X_START(6),.X_END(28),.Y_START(8),.Y_END(617)) dut(.*);
    always @(negedge clk) begin
        if(reset)begin t=0;sample_ce=0;hs_n_sampled=1;vs_n_async=1;rgb_sampled=0;end
        else begin
            sample_ce=t%2==0;hs_n_sampled=no_hs || t%(2*N)>=4;
            vs_n_async=no_vs || t%(N*FL)<10 || t%(N*FL)>=30;
            rgb_sampled=t/2;t=t+1;
        end
    end
    always @(posedge clk) begin
        #1;
        if(blank_n)begin
            source_line=(t-1-3)/(2*N)-1;source_x=(t-1-3)%N;
            expected=source_line*N+source_x;
            if(rgb!==expected || !sync_valid || protocol_error || !hs_n)
                $fatal(1,"Integrated pixel mismatch t=%0d actual=%h expected=%h",t-1,rgb,expected);
            checked=checked+1;
        end else if(rgb!==0) $fatal(1,"RGB not masked");
        if(!sync_valid && blank_n) $fatal(1,"Invalid sync visible");
    end
    task ticks(input integer count);repeat(count)begin @(posedge clk);#2;end endtask
    integer before_count;
    initial begin
        ticks(4);reset=0;ticks(6*N*FL);
        if(checked<40000) $fatal(1,"Too little active video %0d",checked);
        no_hs=1;ticks(2*N+4);if(sync_valid || blank_n) $fatal(1,"HS loss remains visible");
        before_count=checked;no_hs=0;ticks(4*N*FL);if(checked<=before_count) $fatal(1,"No HS recovery");
        no_vs=1;ticks(661*N);if(sync_valid || blank_n) $fatal(1,"VS loss remains visible");
        before_count=checked;no_vs=0;ticks(4*N*FL);if(checked<=before_count) $fatal(1,"No VS recovery");
        $display("PASS stream_input_video: %0d independently calculated visible pixels; FPGA RGB blanking and H/V loss/recovery",checked);
        $finish;
    end
    initial begin #20000000;$fatal(1,"Timeout");end
endmodule
