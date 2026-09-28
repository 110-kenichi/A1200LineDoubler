`timescale 1ns/1ps
// Single-master, one 7-bit-address / 8-bit-register / 8-bit-data write.
// Drive pins only through: assign scl = scl_low ? 1'b0 : 1'bz;
//                         assign sda = sda_low ? 1'b0 : 1'bz;
// Raw pad inputs are synchronized here. No driven logic-high output.
// start is accepted only when !busy. done pulses once; error persists until
// the next accepted command. 1/2/3 = NACK address/register/data, 4 = timeout.
// A timeout releases both pins; a physical STOP cannot be guaranteed on a
// stuck bus. The caller must reset the peripheral before attempting recovery.
module i2c_register_write #(
    parameter integer HALF_CYCLES = 135, // 27 MHz -> <=100 kHz
    parameter integer TIMEOUT_CYCLES = 270000
)(
    input wire clk, reset, start,
    input wire [6:0] address,
    input wire [7:0] register_address, write_data,
    input wire scl_in, sda_in,
    output reg scl_low, sda_low, busy, done,
    output reg [2:0] error
);
    localparam IDLE=0, FREE=1, START_HOLD=2, BIT_LOW=3, BIT_RISE=4,
        BIT_HIGH=5, ACK_LOW=6, ACK_RISE=7, ACK_HIGH=8,
        STOP_LOW=9, STOP_RISE=10, STOP_HIGH=11, STOP_FREE=12;
    reg [3:0] state;
    reg [7:0] bytes [0:2];
    reg [1:0] byte_index;
    reg [2:0] bit_index;
    reg scl_meta, scl_sync, sda_meta, sda_sync;
    localparam TW = $clog2(TIMEOUT_CYCLES+1);
    localparam HW = $clog2(HALF_CYCLES+1);
    reg [TW-1:0] watchdog;
    reg [HW-1:0] count;
    wire waiting = state==FREE || state==BIT_RISE || state==ACK_RISE || state==STOP_RISE;
    initial begin
        if (HALF_CYCLES < 4 || TIMEOUT_CYCLES <= 4*HALF_CYCLES)
            $fatal(1,"Invalid I2C timing parameters");
    end
    always @(posedge clk) begin
        if (reset) begin
            scl_meta<=1; scl_sync<=1; sda_meta<=1; sda_sync<=1;
        end else begin
            scl_meta<=scl_in; scl_sync<=scl_meta;
            sda_meta<=sda_in; sda_sync<=sda_meta;
        end
    end
    always @(posedge clk) begin
        if (reset) begin
            state<=IDLE; scl_low<=0; sda_low<=0; busy<=0; done<=0;
            error<=0; watchdog<=0; count<=0; byte_index<=0; bit_index<=7;
            bytes[0]<=0; bytes[1]<=0; bytes[2]<=0;
        end else begin
            done<=0;
            if (waiting) watchdog<=watchdog+1'b1;
            else watchdog<=0;
            if (waiting && watchdog==TIMEOUT_CYCLES-1) begin
                state<=IDLE; busy<=0; done<=1; error<=4;
                scl_low<=0; sda_low<=0; watchdog<=0; count<=0;
            end else case (state)
                IDLE: if (start) begin
                    bytes[0]<={address,1'b0}; bytes[1]<=register_address; bytes[2]<=write_data;
                    byte_index<=0; bit_index<=7; error<=0; busy<=1;
                    count<=0; watchdog<=0; state<=FREE;
                end
                FREE: begin
                    if (scl_sync && sda_sync) begin
                        if (count==HALF_CYCLES-1) begin
                            count<=0; watchdog<=0; sda_low<=1; state<=START_HOLD;
                        end else count<=count+1'b1;
                    end else count<=0;
                end
                START_HOLD: if (count==HALF_CYCLES-1) begin
                    count<=0; scl_low<=1; sda_low<=!bytes[0][7]; state<=BIT_LOW;
                end else count<=count+1'b1;
                BIT_LOW: if (count==HALF_CYCLES-1) begin
                    count<=0; scl_low<=0; watchdog<=0; state<=BIT_RISE;
                end else count<=count+1'b1;
                BIT_RISE: if (scl_sync) begin count<=0; state<=BIT_HIGH; end
                BIT_HIGH: if (count==HALF_CYCLES-1) begin
                    count<=0; scl_low<=1;
                    if (bit_index==0) begin sda_low<=0; state<=ACK_LOW; end
                    else begin
                        bit_index<=bit_index-1'b1;
                        sda_low<=!bytes[byte_index][bit_index-1'b1]; state<=BIT_LOW;
                    end
                end else count<=count+1'b1;
                ACK_LOW: if (count==HALF_CYCLES-1) begin
                    count<=0; scl_low<=0; watchdog<=0; state<=ACK_RISE;
                end else count<=count+1'b1;
                ACK_RISE: if (scl_sync) begin count<=0; state<=ACK_HIGH; end
                ACK_HIGH: if (count==HALF_CYCLES-1) begin
                    count<=0; scl_low<=1;
                    if (sda_sync) begin
                        error<={1'b0,byte_index}+3'd1; sda_low<=1; state<=STOP_LOW;
                    end else if (byte_index==2) begin sda_low<=1; state<=STOP_LOW; end
                    else begin
                        byte_index<=byte_index+1'b1; bit_index<=7;
                        sda_low<=!bytes[byte_index+1'b1][7]; state<=BIT_LOW;
                    end
                end else count<=count+1'b1;
                STOP_LOW: if (count==HALF_CYCLES-1) begin
                    count<=0; scl_low<=0; watchdog<=0; state<=STOP_RISE;
                end else count<=count+1'b1;
                STOP_RISE: if (scl_sync) begin count<=0; state<=STOP_HIGH; end
                STOP_HIGH: if (count==HALF_CYCLES-1) begin
                    count<=0; sda_low<=0; state<=STOP_FREE;
                end else count<=count+1'b1;
                STOP_FREE: if (count==HALF_CYCLES-1) begin
                    count<=0; state<=IDLE; busy<=0; done<=1;
                end else count<=count+1'b1;
                default: begin state<=IDLE; scl_low<=0; sda_low<=0; busy<=0; error<=4; done<=1; end
            endcase
        end
    end
endmodule
