`timescale 1ns/1ps
module tb_clock_recovery_system;
    reg clk_ref=0,adc_clock=0,video_clock=0,reset=1,qualified_ref=0,pll_lock=0;
    reg adc_running=1,video_running=1,never_lock=0;
    wire pll_reset,reset_video,output_permitted,dac_psave_n,run_ref,input_stable;
    wire [2:0] fault_history;
    integer lock_count=0,checks=0;
    always #18.5 clk_ref=~clk_ref;
    always begin #18;if(adc_running)adc_clock=~adc_clock;end
    // A ratio-correct ideal source, independently stoppable to inject a fault.
    always begin #9;if(video_running)video_clock=~video_clock;end
    clock_recovery_system #(.GOOD_INTERVALS(3),.RESET_HOLD_CYCLES(10),.LOCK_TIMEOUT_CYCLES(800)) dut(.*);
    always @(negedge clk_ref)begin
        if(pll_reset || never_lock)begin pll_lock=0;lock_count=0;end
        else if(lock_count==8)pll_lock=1;
        else lock_count=lock_count+1;
    end
    task ticks(input integer n);repeat(n)begin @(posedge clk_ref);#1;end endtask
    task dark;
        begin
            if(output_permitted || dac_psave_n || !reset_video) $fatal(1,"Output not inhibited");
            checks=checks+1;
        end
    endtask
    task acquire;
        integer n;
        begin
            n=0;while(!run_ref && n<3000)begin ticks(1);n=n+1;end
            if(!run_ref || !output_permitted || !dac_psave_n || reset_video) $fatal(1,"Acquisition deadlock");
            checks=checks+1;
        end
    endtask
    initial begin
        ticks(5);reset=0;ticks(200);dark();qualified_ref=1;acquire();
        video_running=0;ticks(90);dark();
        if(!pll_reset && run_ref) $fatal(1,"Video failure not handed to restart controller");
        video_running=1;acquire();
        adc_running=0;ticks(175);dark();if(!pll_reset) $fatal(1,"ADC stop not resetting PLL");
        adc_running=1;acquire();
        never_lock=1;ticks(1000);dark();if(!fault_history[2]) $fatal(1,"No lock timeout");
        never_lock=0;acquire();
        qualified_ref=0;#1;dark();ticks(5);qualified_ref=1;acquire();
        $display("PASS clock_recovery_system: %0d checks; real watchdog/lifecycle feedback, startup, stopped ADC/video clocks, lock timeout, requalification",checks);
        $finish;
    end
    initial begin #1000000;$fatal(1,"Timeout");end
endmodule
