`timescale 1ns/1ps
// Functional integration boundary. Not a pin-mapped board top: POR, physical
// I/O, actual rPLL instance, DAC clock forwarding and timing constraints remain
// external. Never replace video_clock with an unrelated free-running clock.
module amiga_logic_core #(
    parameter integer H_SAMPLES=0,VS_ALIGN_CYCLES=-1,
    parameter integer HS_WIDTH=0,X_START=0,X_END=0,Y_START=0,Y_END=0,
    parameter integer I2C_HALF=135,I2C_TIMEOUT=270000,
    parameter integer POWER_WAIT=135000,ADC_RESET_HOLD=270,ADC_SETTLE=27000,ALC_WAIT=810000,
    parameter integer PLL_GOOD=8,PLL_RESET_HOLD=270,PLL_TIMEOUT=270000
)(
    input wire clk_ref,reset,power_good,
    input wire adc_clock,video_clock,pll_lock,
    input wire [23:0] adc_rgb,
    input wire adc_hs_n,adc_vs_n,scl_in,sda_in,
    output wire adc_reset_n,adc_pwdn,scl_low,sda_low,pll_reset,
    output wire [23:0] dac_rgb,
    output wire dac_blank_n,dac_psave_n,hs_out_n,vs_out_n,
    output wire configured_ref,video_ready_ref,configuration_fault,
    output wire [2:0] write_error,clock_fault_history,sync_fault_history,
    output wire [7:0] failed_register
);
    wire clock_run,input_stable,reset_video,permit;
    wire ce,capture_reset,hs_sampled,sync_valid,protocol_error;
    wire [23:0] captured_rgb,stream_rgb;
    wire stream_blank,stream_hs,stream_vs;
    (* ASYNC_REG="TRUE" *) reg [1:0] video_sync;
    wire video_good=sync_valid && !protocol_error;
    always @(posedge clk_ref or posedge reset_video)
        if(reset_video)video_sync<=0;
        else video_sync<={video_sync[0],video_good};
    tvp7002_boot #(.H_SAMPLES(H_SAMPLES),.HALF_CYCLES(I2C_HALF),.TIMEOUT_CYCLES(I2C_TIMEOUT),
      .POWER_WAIT_CYCLES(POWER_WAIT),.RESET_CYCLES(ADC_RESET_HOLD),.SETTLE_CYCLES(ADC_SETTLE),
      .ALC_WAIT_CYCLES(ALC_WAIT)) boot
      (.clk(clk_ref),.reset(reset),.power_good(power_good),.video_locked(clock_run && video_sync[1]),
       .scl_in(scl_in),.sda_in(sda_in),.adc_reset_n(adc_reset_n),.adc_pwdn(adc_pwdn),
       .scl_low(scl_low),.sda_low(sda_low),.qualified_ref(configured_ref),.video_allowed(video_ready_ref),
       .fault(configuration_fault),.write_error(write_error),.failed_register(failed_register));
    clock_recovery_system #(.GOOD_INTERVALS(PLL_GOOD),.RESET_HOLD_CYCLES(PLL_RESET_HOLD),
      .LOCK_TIMEOUT_CYCLES(PLL_TIMEOUT)) clocks
      (.clk_ref(clk_ref),.adc_clock(adc_clock),.video_clock(video_clock),.reset(reset),
       .qualified_ref(configured_ref),.pll_lock(pll_lock),.pll_reset(pll_reset),
       .reset_video(reset_video),.output_permitted(permit),.dac_psave_n(dac_psave_n),
       .run_ref(clock_run),.input_stable(input_stable),.fault_history(clock_fault_history));
    adc_rgb_capture capture
      (.adc_clock(adc_clock),.video_clock(video_clock),.reset(reset_video),.adc_rgb(adc_rgb),
       .adc_hs_n(adc_hs_n),.rgb_sampled(captured_rgb),.hs_n_sampled(hs_sampled),
       .sample_ce(ce),.stream_reset(capture_reset));
    stream_input_video #(.H_SAMPLES(H_SAMPLES),.VS_ALIGN_CYCLES(VS_ALIGN_CYCLES),
      .HS_WIDTH(HS_WIDTH),.X_START(X_START),.X_END(X_END),.Y_START(Y_START),.Y_END(Y_END)) video
      (.clk(video_clock),.reset(capture_reset),.sample_ce(ce),.hs_n_sampled(hs_sampled),
       .vs_n_async(adc_vs_n),.rgb_sampled(captured_rgb),.rgb(stream_rgb),.blank_n(stream_blank),
       .hs_n(stream_hs),.vs_n(stream_vs),.sync_valid(sync_valid),.protocol_error(protocol_error),
       .fault_history(sync_fault_history));
    // One matched video-cycle delay for RGB, blank and both sync signals.
    // Guard permission asserts only after the video-domain reset release.
    dac_output_stage output_stage
      (.clk(video_clock),.reset(reset),.permit(permit),.valid(video_good),.rgb_in(stream_rgb),
       .blank_in(stream_blank),.hs_in(stream_hs),.vs_in(stream_vs),
       .rgb(dac_rgb),.blank_n(dac_blank_n),.hs_n(hs_out_n),.vs_n(vs_out_n));
endmodule
