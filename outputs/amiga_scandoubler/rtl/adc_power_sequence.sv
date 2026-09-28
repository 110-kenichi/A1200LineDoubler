`timescale 1ns/1ps
// Run from the always-on 27 MHz reference, never from ADC DATACLK.
// power_good must represent all required rails. Synchronizer prevents a
// direct asynchronous input driving the sequence. Board pull resistors keep
// RESETB low and PWDN high before FPGA configuration.
// No I2C transaction is permitted until config_allowed. Any configuration
// error latches FAULT until reset or power loss; video_allowed additionally requires the
// video/PLL lock detector supplied by the caller.
module adc_power_sequence #(
    parameter integer POWER_WAIT_CYCLES=135000, // 5 ms at 27 MHz
    parameter integer RESET_CYCLES=270, // 10 us (> datasheet 1 us minimum)
    parameter integer SETTLE_CYCLES=27000 // conservative 1 ms, not a lock indication
)(
    input wire clk, reset, power_good,
    input wire config_done, config_error, video_locked,
    output reg adc_reset_n, adc_pwdn, config_allowed,
    output wire video_allowed,
    output reg fault
);
    localparam WAIT_POWER=0, RESET_ADC=1, SETTLE=2, CONFIGURE=3, RUN=4, FAULT=5;
    localparam MAX1=POWER_WAIT_CYCLES>RESET_CYCLES?POWER_WAIT_CYCLES:RESET_CYCLES;
    localparam MAX2=MAX1>SETTLE_CYCLES?MAX1:SETTLE_CYCLES;
    reg [$clog2(MAX2+1)-1:0] count;
    reg [2:0] state;
    reg pg_meta, pg_sync;
    assign video_allowed=(state==RUN) && pg_sync && video_locked && !config_error;
    initial begin
        if (POWER_WAIT_CYCLES<2 || RESET_CYCLES<2 || SETTLE_CYCLES<2)
            $fatal(1,"ADC power timing parameters must be >=2");
    end
    always @(posedge clk) begin
        if (reset) begin pg_meta<=0; pg_sync<=0; end
        else begin pg_meta<=power_good; pg_sync<=pg_meta; end
    end
    always @(posedge clk) begin
        if (reset) begin
            state<=WAIT_POWER; count<=0; adc_reset_n<=0; adc_pwdn<=1;
            config_allowed<=0; fault<=0;
        end else if (!pg_sync) begin
            // A power interruption requires the complete startup sequence.
            state<=WAIT_POWER; count<=0; adc_reset_n<=0; adc_pwdn<=1;
            config_allowed<=0; fault<=0;
        end else case (state)
            WAIT_POWER: if (count==POWER_WAIT_CYCLES-1) begin
                count<=0; adc_pwdn<=0; state<=RESET_ADC;
            end else count<=count+1'b1;
            RESET_ADC: if (count==RESET_CYCLES-1) begin
                count<=0; adc_reset_n<=1; state<=SETTLE;
            end else count<=count+1'b1;
            SETTLE: if (count==SETTLE_CYCLES-1) begin
                count<=0; config_allowed<=1; state<=CONFIGURE;
            end else count<=count+1'b1;
            CONFIGURE: if (config_error) begin
                config_allowed<=0; fault<=1; state<=FAULT;
            end else if (config_done) begin config_allowed<=0; state<=RUN; end
            RUN: if (config_error) begin fault<=1; state<=FAULT; end
            FAULT: begin adc_reset_n<=0; adc_pwdn<=1; config_allowed<=0; end
            default: begin state<=FAULT; fault<=1; config_allowed<=0; end
        endcase
    end
endmodule
