`timescale 1ns/1ps
module tb_dac_output_stage;
    reg clk=0, run=1, reset=0, permit=1, valid=0, blank_in=0, hs_in=1, vs_in=1;
    reg [23:0] rgb_in=0;
    wire [23:0] rgb;
    wire blank_n,hs_n,vs_n;
    reg [26:0] expected;
    integer i,offset,checks=0;
    dac_output_stage dut(.*);
    always #9 if(run) clk=~clk;
    task check;
        input [26:0] value;
        begin
            if({rgb,blank_n,hs_n,vs_n}!==value) $fatal(1,"output alignment/stability mismatch");
            checks=checks+1;
        end
    endtask
    initial begin
        #1;permit=0;#1;check({24'b0,3'b011});
        @(posedge clk);#1;permit=1;
        repeat(2)begin @(posedge clk);#1;check({24'b0,3'b011});end
        for(i=0;i<256;i=i+1)begin
            @(negedge clk);
            rgb_in=24'h123456 ^ (i*24'h010307);
            valid=(i%7)!=0;blank_in=(i%5)!=0;hs_in=i[1];vs_in=i[3];
            expected={(valid && blank_in)?rgb_in:24'b0,valid && blank_in,hs_in,vs_in};
            @(posedge clk);#1;check(expected);
            rgb_in=~rgb_in;blank_in=~blank_in;hs_in=~hs_in;vs_in=~vs_in;
            #2;check(expected);
        end
        // No video edge is available to clear stale visible output.
        @(negedge clk);valid=1;blank_in=1;rgb_in=24'habcdef;
        @(posedge clk);#1;run=0;permit=0;#1;check({24'b0,3'b011});
        #100;check({24'b0,3'b011});
        run=1;@(posedge clk);#1;permit=1;
        repeat(2)begin @(posedge clk);#1;check({24'b0,3'b011});end
        @(negedge clk);rgb_in=24'hfedcba;hs_in=0;vs_in=1;
        @(posedge clk);#1;check({24'hfedcba,3'b101});
        // Exercise release at each integer-ns offset across a full period.
        for(offset=1;offset<18;offset=offset+1)begin
            @(negedge clk);#1;permit=0;#1;check({24'b0,3'b011});
            @(posedge clk);#(offset);permit=1;
            repeat(2)begin @(posedge clk);#1;check({24'b0,3'b011});end
            @(posedge clk);#1;check({24'hfedcba,3'b101});
        end
        // Permission returning without clock edges must not release output.
        @(negedge clk);#1;run=0;reset=1;#1;check({24'b0,3'b011});
        #3;reset=0;#100;check({24'b0,3'b011});
        run=1;repeat(2)begin @(posedge clk);#1;check({24'b0,3'b011});end
        @(posedge clk);#1;check({24'hfedcba,3'b101});
        $display("PASS dac_output_stage: %0d alignment, stability, stopped-clock clear and restart checks",checks);
        $finish;
    end
    initial begin #100000;$fatal(1,"timeout");end
endmodule
