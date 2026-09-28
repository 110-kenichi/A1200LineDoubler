`timescale 1ns/1ps
module tb_adc_rgb_capture;
    parameter integer PERIOD_PS=36000,DATA_DELAY_PS=1500,DUTY_PERCENT=50,PHASE_DEGREES=180;
    localparam real ADC_PERIOD=PERIOD_PS/1000.0;
    localparam real VIDEO_PERIOD=ADC_PERIOD/2;
    reg adc_clock=0,video_clock=0,reset=1,running=1;
    reg [23:0] adc_rgb=0;
    reg adc_hs_n=1;
    wire [23:0] rgb_sampled;
    wire hs_n_sampled,sample_ce,stream_reset;
    integer sent=0,checks=0,last_id=-1,cycle=0,last_cycle=-1;
    reg [23:0] data_for_id;
    adc_rgb_capture dut(.*);
    initial forever begin
        adc_clock=1;#(ADC_PERIOD*DUTY_PERCENT/100.0);
        adc_clock=0;#(ADC_PERIOD*(100-DUTY_PERCENT)/100.0);
    end
    initial begin
        #(VIDEO_PERIOD*PHASE_DEGREES/360.0);
        forever begin video_clock=1;#(VIDEO_PERIOD/2);video_clock=0;#(VIDEO_PERIOD/2);end
    end
    function [23:0] pattern(input integer id);
        pattern={8'(id),8'(id^8'ha5),8'(~id)};
    endfunction
    always @(posedge adc_clock) begin
        sent=sent+1;
        #(DATA_DELAY_PS/1000.0);
        adc_rgb=pattern(sent);adc_hs_n=sent%16>=3;
    end
    // Observe exactly as the synchronous stream consumer does, before NBA.
    always @(posedge video_clock) begin
        cycle=cycle+1;
        if(stream_reset)begin last_id=-1;last_cycle=-1;end
        else if(sample_ce) begin
            if(last_cycle>=0 && cycle-last_cycle!=2) $fatal(1,"Sample cadence mismatch");
            if(last_id>=0 && rgb_sampled!==pattern(last_id+1)) $fatal(1,"Pixel split/dropped/repeated");
            if(rgb_sampled[15:8]!=(rgb_sampled[23:16]^8'ha5) || rgb_sampled[7:0]!=8'(~rgb_sampled[23:16]))
                $fatal(1,"Mixed RGB bits");
            if(hs_n_sampled!==(rgb_sampled[23:16]%16>=3)) $fatal(1,"HS/RGB misaligned");
            last_id=rgb_sampled[23:16];last_cycle=cycle;checks=checks+1;
        end
    end
    initial begin
        #101;reset=0;
        repeat(120)@(negedge adc_clock);
        #1;reset=1;#1;
        if(!stream_reset || sample_ce) $fatal(1,"Asynchronous reset failed");
        #83;reset=0;
        repeat(120)@(negedge adc_clock);
        if(checks<200) $fatal(1,"Insufficient samples");
        $display("PASS adc_rgb_capture PERIOD_PS=%0d DATA_DELAY_PS=%0d DUTY=%0d PHASE=%0d: %0d coherent RGB/HS samples, every-other-cycle cadence, asynchronous reset/restart",PERIOD_PS,DATA_DELAY_PS,DUTY_PERCENT,PHASE_DEGREES,checks);
        $finish;
    end
    initial begin #100000;$fatal(1,"Timeout");end
endmodule
