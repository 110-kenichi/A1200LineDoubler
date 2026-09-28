`timescale 1ns/1ps
module tb_video_clock_guard;
    reg clk_ref=0,clk_video=0,reset=1,qualified_ref=0,pll_lock=0;
    reg running=1;
    integer half_video=9,checks=0;
    wire reset_video,output_permitted,ready_ref,dac_psave_n;
    always #18.5 clk_ref=~clk_ref;
    always begin #(half_video); if(running) clk_video=~clk_video;end
    video_clock_guard dut(.*);
    time last_edge;
    always @(posedge clk_video) last_edge=$time;
    always @(negedge reset_video) begin
        if($time>0 && $time!=last_edge) $fatal(1,"Reset release not on video edge");
    end
    task ref_wait(input integer n);repeat(n) @(negedge clk_ref);endtask
    task acquire;
        integer n;
        begin
            n=0;
            while(!ready_ref && n<1200) begin ref_wait(1);n=n+1;end
            if(!ready_ref || reset_video || !output_permitted) $fatal(1,"Acquisition failed");
            checks=checks+1;
        end
    endtask
    task denied;
        begin
            if(!reset_video || output_permitted || dac_psave_n) $fatal(1,"Unsafe permission");
            checks=checks+1;
        end
    endtask
    initial begin
        #100;reset=0;ref_wait(100);denied();
        qualified_ref=1;ref_wait(100);denied();
        pll_lock=1;ref_wait(150);denied();acquire();
        // Remain stable across many fractional reference/video phase alignments.
        repeat(1500) begin ref_wait(1);if(!ready_ref) $fatal(1,"False clock loss");checks=checks+1;end
        // Stop at a high clock level, with PLL LOCK deliberately stuck high.
        @(posedge clk_video);#1;running=0;
        ref_wait(85);denied();ref_wait(4);if(ready_ref) $fatal(1,"Stale ready");
        running=1;acquire();
        // Stop low, then drop qualification without either video edge.
        @(negedge clk_video);#1;running=0;qualified_ref=0;#1;denied();
        qualified_ref=1;ref_wait(300);denied();running=1;acquire();
        pll_lock=0;#1;denied();pll_lock=1;ref_wait(150);denied();acquire();
        half_video=4;ref_wait(400);denied();
        half_video=16;ref_wait(500);denied();
        half_video=9;acquire();
        reset=1;#1;denied();ref_wait(5);reset=0;acquire();
        $display("PASS video_clock_guard: %0d checks; acquisition, phase drift, stopped high/low, stuck LOCK, qualification/LOCK loss, fast/slow clock, reset and reacquisition",checks);
        $finish;
    end
    initial begin #1000000;$fatal(1,"Timeout");end
endmodule
