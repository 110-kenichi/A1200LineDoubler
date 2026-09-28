`timescale 1ns/1ps
// Development core, not a complete board bitstream.
// clk: phase-related 2x ADC sample clock. sample_ce: exactly every other clk.
// line_start: one clk pulse coincident with sample_ce and sample zero.
// H_SAMPLES includes blanking. Reset on PLL unlock or profile changes.
// No asynchronous input may be connected directly to this module.
module line_double #(
    parameter integer H_SAMPLES = 1816,
    parameter integer PIXEL_BITS = 24,
    parameter integer AW = $clog2(H_SAMPLES)
)(
    input wire clk, reset, sample_ce, line_start,
    input wire [PIXEL_BITS-1:0] pixel_in,
    output wire [PIXEL_BITS-1:0] pixel_out,
    output reg pixel_valid, out_sol,
    output reg [AW-1:0] out_x,
    output reg protocol_error
);
    (* ram_style = "block" *) reg [PIXEL_BITS-1:0] bank0 [0:H_SAMPLES-1];
    (* ram_style = "block" *) reg [PIXEL_BITS-1:0] bank1 [0:H_SAMPLES-1];
    reg [PIXEL_BITS-1:0] bank0_q, bank1_q;
    reg started, write_bank, read_bank, reading;
    reg [AW:0] written;
    reg [AW-1:0] read_x;
    reg [AW+1:0] elapsed;
    reg previous_ce;

    // Exactly one synchronous read and one write port per bank. The read
    // registers intentionally have no reset, so synthesis can use block RAM.
    // pixel_valid masks startup data and faults. The bank being written is
    // never selected for visible output, including bank-switch cycle zero.
    wire [AW-1:0] ram_read_address = line_start ? {AW{1'b0}} : read_x;
    wire [AW-1:0] ram_write_address = line_start ? {AW{1'b0}} : written[AW-1:0];
    wire ram_write_bank = line_start ? (started ? !write_bank : 1'b0) : write_bank;
    wire ram_write_enable = !reset && sample_ce &&
                            (line_start || (started && written < H_SAMPLES));
    always @(posedge clk) begin
        bank0_q <= bank0[ram_read_address];
        bank1_q <= bank1[ram_read_address];
        if(ram_write_enable && !ram_write_bank) bank0[ram_write_address] <= pixel_in;
        if(ram_write_enable &&  ram_write_bank) bank1[ram_write_address] <= pixel_in;
    end
    assign pixel_out = pixel_valid ? (read_bank ? bank1_q : bank0_q) : {PIXEL_BITS{1'b0}};

    initial begin
        if (H_SAMPLES < 4 || (H_SAMPLES % 2) != 0)
            $fatal(1, "H_SAMPLES must be even and at least four");
    end

    always @(posedge clk) begin
        if (reset) begin
            started <= 0; write_bank <= 0; read_bank <= 0;
            reading <= 0; written <= 0; read_x <= 0; elapsed <= 0;
            previous_ce <= 0; pixel_valid <= 0;
            out_sol <= 0; out_x <= 0; protocol_error <= 0;
        end else begin
            pixel_valid <= 0; out_sol <= 0;
            previous_ce <= sample_ce;
            if (started && (sample_ce == previous_ce)) begin
                protocol_error <= 1;
                reading <= 0;
            end
            if (line_start) begin
                // Read the completed bank before switching the write bank.
                if (started && sample_ce && written == H_SAMPLES &&
                    elapsed == 2*H_SAMPLES-1 && !protocol_error &&
                    sample_ce != previous_ce) begin
                    pixel_valid <= 1; out_sol <= 1; out_x <= 0;
                    read_bank <= write_bank; read_x <= 1; reading <= 1;
                end else begin
                    reading <= 0;
                    if (started || !sample_ce) protocol_error <= 1;
                end
                if (started) write_bank <= !write_bank;
                else write_bank <= 0;
                started <= 1; written <= sample_ce ? 1 : 0; elapsed <= 0;
            end else if (started) begin
                if (elapsed < 2*H_SAMPLES) elapsed <= elapsed + 1'b1;
                if (sample_ce && written < H_SAMPLES) begin
                    written <= written + 1'b1;
                end
                if (reading && !protocol_error && elapsed < 2*H_SAMPLES-1 &&
                    sample_ce != previous_ce) begin
                    pixel_valid <= 1; out_sol <= read_x == 0; out_x <= read_x;
                    if (read_x == H_SAMPLES-1) read_x <= 0;
                    else read_x <= read_x + 1'b1;
                end
                if (elapsed >= 2*H_SAMPLES-1) begin
                    protocol_error <= 1; reading <= 0;
                end
            end
        end
    end
endmodule
