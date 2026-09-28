`timescale 1ns/1ps
module tb_adc_power_sequence;
    reg clk=0,reset=1,power_good=0,config_done=0,config_error=0,video_locked=0;
    always #5 clk=~clk;
    wire adc_reset_n,adc_pwdn,config_allowed,video_allowed,fault;
    adc_power_sequence #(.POWER_WAIT_CYCLES(12),.RESET_CYCLES(4),.SETTLE_CYCLES(6)) dut(.*);
    task ticks(input integer n);begin repeat(n) @(negedge clk);end endtask
    task init;
      begin reset=1;power_good=0;config_done=0;config_error=0;video_locked=0;ticks(4);reset=0;ticks(4);end
    endtask
    task ready;
      integer t;
      begin
        power_good=1;t=0;
        while(!config_allowed && t<50) begin ticks(1);t=t+1;end
        if(t<22 || t==50 || adc_pwdn || !adc_reset_n || video_allowed)
          $fatal(1,"Bad startup sequence t=%0d",t);
      end
    endtask
    integer n;
    initial begin
        init();ticks(40);
        if(adc_reset_n || !adc_pwdn || config_allowed || video_allowed) $fatal(1,"Started without power");
        ready();ticks(10);
        if(video_allowed) $fatal(1,"Video before config");
        config_done=1;ticks(1);config_done=0;
        if(video_allowed || config_allowed) $fatal(1,"Video before lock");
        video_locked=1;ticks(1);
        if(!video_allowed) $fatal(1,"Video not enabled");
        video_locked=0;#1;
        if(video_allowed) $fatal(1,"Lost lock still visible");
        $display("PASS ADC power: power wait, reset hold, settle, config and video lock gating");
        power_good=0;ticks(4);
        if(adc_reset_n || !adc_pwdn || video_allowed) $fatal(1,"Power loss not handled");
        ready();config_error=1;ticks(2);
        if(!fault || config_allowed || video_allowed || adc_reset_n || !adc_pwdn) $fatal(1,"Fault not safe");
        config_error=0;config_done=1;video_locked=1;ticks(30);
        if(!fault || video_allowed) $fatal(1,"Fault not latched");
        $display("PASS ADC power: brownout restarts, config error latches safe state");
        init();power_good=1;ticks(8);power_good=0;ticks(4);
        if(adc_reset_n || !adc_pwdn || config_allowed) $fatal(1,"Unstable power accepted");
        ready();
        $display("PASS ADC power: interrupted power qualification restarts full delay");
        $finish;
    end
    initial begin #50000;$fatal(1,"test watchdog");end
endmodule
