`timescale 1ns/1ps
// Board-specific RGB/HSYNC_A/VSYNC_A startup candidate. Not calibrated.
// H_SAMPLES must be selected explicitly. Run entirely from 27 MHz.
// Configuration success means ACKed writes + settling, NOT register readback
// or proof of ADC lock. Reset the whole sequence on a profile change.
module tvp7002_boot #(
    parameter integer H_SAMPLES=0,
    parameter integer SAMPLE_PHASE=0,
    parameter integer CLAMP_START=6,CLAMP_WIDTH=16,ALC_START=24,
    parameter integer ADC_HS_WIDTH=128,
    parameter integer HALF_CYCLES=135,TIMEOUT_CYCLES=270000,
    parameter integer POWER_WAIT_CYCLES=135000,RESET_CYCLES=270,SETTLE_CYCLES=27000,
    parameter integer ALC_WAIT_CYCLES=810000
)(
    input wire clk,reset,power_good,video_locked,scl_in,sda_in,
    output wire adc_reset_n,adc_pwdn,scl_low,sda_low,
    output wire qualified_ref,video_allowed,fault,
    output reg [2:0] write_error,
    output reg [7:0] failed_register
);
    localparam COUNT=36;
    localparam IDLE=0,ISSUE=1,WAIT_WRITE=2,SETTLE_ALC=3,COMPLETE=4,FAILED=5;
    reg [2:0] state;
    reg [5:0] index;
    reg [$clog2(ALC_WAIT_CYCLES+1)-1:0] wait_count;
    reg start,config_done,config_error;
    wire config_allowed,busy,done;
    wire [2:0] error;
    reg [15:0] entry;
    wire transaction_reset=reset || !adc_reset_n || adc_pwdn;
    initial begin
        if(H_SAMPLES<1536 || H_SAMPLES>2048 || H_SAMPLES%2 ||
           SAMPLE_PHASE<0 || SAMPLE_PHASE>31 || CLAMP_START<1 ||
           CLAMP_WIDTH<1 || ALC_START<CLAMP_START+CLAMP_WIDTH ||
           ALC_START>255 || ADC_HS_WIDTH<1 || ADC_HS_WIDTH>255 || ALC_WAIT_CYCLES<2)
            $fatal(1,"Explicit valid TVP7002 candidate profile required");
    end
    always @* begin
        case(index)
          0:entry=16'h1703; // Outputs high impedance during setup.
          1:entry=16'h1900; // R/G/B input 1.
          2:entry=16'h1aca; // External 27MHz reference, HPLL samples, H/V input A.
          3:entry=16'h0e12; // Discrete H/V, automatic H polarity, low HS output.
          4:entry=16'h0f2e; // Internal clamp/coast source, normal power, no ADC test.
          5:entry=16'h1058; // All RGB channels bottom-level clamped.
          6:entry=16'h1500; // RGB full range 4:4:4, no embedded sync, trailing clamp.
          7:entry=16'h1800; // CSC off, launch data on DATACLK rising edge.
          8:entry={8'h01,8'(H_SAMPLES>>4)}; // Divider MSB must be written first.
          9:entry={8'h02,8'((H_SAMPLES&15)<<4)};
         10:entry=16'h0310; // <36MHz VCO range, charge-pump code 2 candidate.
         11:entry={8'h04,8'(SAMPLE_PHASE<<3)}; // No divide-by-two.
         12:entry={8'h05,8'(CLAMP_START)};
         13:entry={8'h06,8'(CLAMP_WIDTH)};
         14:entry={8'h07,8'(ADC_HS_WIDTH)};
         15:entry=16'h210d; // 5+13 = 18 clocks nominal RGB latency at phase zero.
         16:entry=16'h2204; // Five-wire input: coast disabled, Macrovision disabled.
         17:entry=16'h3602; // Raw VS bypass only. HS remains processed.
         18:entry=16'h1b88; // RGB analog gain 1.3 (700mV nominal input candidate).
         19:entry=16'h1c08;
         20:entry=16'h0819; // Digital gain 1+25/256; calibrate against test pattern.
         21:entry=16'h0919;
         22:entry=16'h0a19;
         23:entry=16'h0b80; // Digital offsets zero (offset binary).
         24:entry=16'h0c80;
         25:entry=16'h0d80;
         26:entry=16'h1d00;
         27:entry=16'h1e10; // Coarse offsets initial +64 ADC counts.
         28:entry=16'h1f10;
         29:entry=16'h2010;
         30:entry=16'h2680; // ALC enabled.
         31:entry=16'h2833; // 1/64 vertical, 16-tap horizontal ALC filter.
         32:entry=16'h2a07; // Fine clamps enabled; preserve reset reserved bits.
         33:entry=16'h2d00; // Coarse clamps disabled.
         34:entry={8'h31,8'(ALC_START)};
         35:entry=16'h1702; // Enable data/clock/sync, keep unused SOGOUT high-Z.
         default:entry=16'h1703;
        endcase
    end
    adc_power_sequence #(.POWER_WAIT_CYCLES(POWER_WAIT_CYCLES),
      .RESET_CYCLES(RESET_CYCLES),.SETTLE_CYCLES(SETTLE_CYCLES)) power_sequence
      (.clk(clk),.reset(reset),.power_good(power_good),.config_done(config_done),
       .config_error(config_error),.video_locked(video_locked),.adc_reset_n(adc_reset_n),
       .adc_pwdn(adc_pwdn),.config_allowed(config_allowed),.video_allowed(video_allowed),.fault(fault));
    i2c_register_write #(.HALF_CYCLES(HALF_CYCLES),.TIMEOUT_CYCLES(TIMEOUT_CYCLES)) writer
      (.clk(clk),.reset(transaction_reset),.start(start),.address(7'h5c),
       .register_address(entry[15:8]),.write_data(entry[7:0]),.scl_in(scl_in),.sda_in(sda_in),
       .scl_low(scl_low),.sda_low(sda_low),.busy(busy),.done(done),.error(error));
    // Independent of video_locked: the clock supervisor may now acquire lock.
    assign qualified_ref=config_done && !config_error && !fault &&
                         adc_reset_n && !adc_pwdn && power_good && !reset;
    always @(posedge clk) begin
        if(reset) begin
            state<=IDLE;index<=0;start<=0;config_done<=0;config_error<=0;
            write_error<=0;failed_register<=0;wait_count<=0;
        end else if(transaction_reset) begin
            state<=IDLE;index<=0;start<=0;config_done<=0;config_error<=0;wait_count<=0;
            // Retain diagnosis through the ADC reset caused by FAULT.
        end else begin
            start<=0;
            case(state)
              IDLE:if(config_allowed) begin
                  index<=0;write_error<=0;failed_register<=0;state<=ISSUE;
              end
              ISSUE:if(!busy) begin start<=1;state<=WAIT_WRITE;end
              WAIT_WRITE:if(done) begin
                  if(error!=0) begin
                      write_error<=error;failed_register<=entry[15:8];
                      config_error<=1;state<=FAILED;
                  end else if(index==COUNT-1) begin wait_count<=0;state<=SETTLE_ALC;end
                  else begin index<=index+1'b1;state<=ISSUE;end
              end
              SETTLE_ALC:if(wait_count==ALC_WAIT_CYCLES-1) begin
                  config_done<=1;state<=COMPLETE;
              end else wait_count<=wait_count+1'b1;
              COMPLETE:;
              FAILED:;
              default:begin config_error<=1;state<=FAILED;end
            endcase
        end
    end
endmodule
