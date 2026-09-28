`timescale 1ns/1ps
module tb_pll_restart_control;
    parameter integer HOLD=10,TIMEOUT=60;
    reg clk_ref=0,adc_clock=0,reset=1,qualified_ref=0,pll_lock=0,video_ready_ref=0;
    wire pll_reset,run_ref,input_stable;
    wire [2:0] fault_history;
    reg adc_running=1,never_lock=0,stuck_lock=0,lose_video=0;
    integer half_adc=18,lock_count=0,ready_count=0,checks=0;
    always #18.5 clk_ref=~clk_ref;
    always begin #(half_adc);if(adc_running)adc_clock=~adc_clock;end
    pll_restart_control #(.GOOD_INTERVALS(3),.RESET_HOLD_CYCLES(HOLD),.LOCK_TIMEOUT_CYCLES(TIMEOUT)) dut(.*);
    // Handshake model only; no analog PLL behavior is claimed.
    always @(negedge clk_ref)begin
        if(stuck_lock)pll_lock=1;
        else if(pll_reset || never_lock)begin pll_lock=0;lock_count=0;end
        else if(lock_count==5)pll_lock=1;
        else lock_count=lock_count+1;
        if(pll_reset || !pll_lock || lose_video)begin video_ready_ref=0;ready_count=0;end
        else if(ready_count==5)video_ready_ref=1;
        else ready_count=ready_count+1;
    end
    task ticks(input integer n);repeat(n)begin @(posedge clk_ref);#1;end endtask
    task acquire;
        integer n;
        begin
            n=0;while(!run_ref && n<TIMEOUT+HOLD+2000)begin ticks(1);n=n+1;end
            if(!run_ref || pll_reset || !input_stable) $fatal(1,"No PLL recovery");
            checks=checks+1;
        end
    endtask
    initial begin
        ticks(5);reset=0;ticks(200);if(!pll_reset) $fatal(1,"PLL enabled before configuration");
        qualified_ref=1;acquire();ticks(500);if(!run_ref) $fatal(1,"False instability");
        adc_running=0;ticks(175);if(!pll_reset || run_ref || !fault_history[0]) $fatal(1,"Stopped ADC not handled");
        adc_running=1;acquire();
        lose_video=1;ticks(4);if(!pll_reset || !fault_history[1]) $fatal(1,"Video-clock failure not handled");
        lose_video=0;acquire();
        half_adc=21;ticks(350);if(run_ref) $fatal(1,"Abrupt frequency change did not requalify");acquire();
        never_lock=1;ticks(TIMEOUT+HOLD+30);if(!fault_history[2] || run_ref) $fatal(1,"Lock timeout not handled");
        never_lock=0;acquire();
        qualified_ref=0;#1;if(!pll_reset || run_ref) $fatal(1,"Permission loss not immediate");
        ticks(5);stuck_lock=1;qualified_ref=1;ticks(1200);
        if(run_ref) $fatal(1,"LOCK stuck high falsely accepted");
        stuck_lock=0;acquire();
        reset=1;#1;if(!pll_reset || run_ref) $fatal(1,"Reset failed");
        $display("PASS pll_restart_control HOLD=%0d TIMEOUT=%0d: %0d acquisition/recovery sequences; ADC stop, frequency step, video-clock loss, timeout, stuck LOCK and reset",HOLD,TIMEOUT,checks);
        $finish;
    end
    initial begin #100000000;$fatal(1,"Timeout");end
endmodule
