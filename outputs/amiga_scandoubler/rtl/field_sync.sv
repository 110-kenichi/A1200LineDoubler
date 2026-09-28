`timescale 1ns/1ps
// Development module: field_start is a clean, synchronous, single-cycle event.
// Delay by one input line, then align to the doubled output line boundary.
// Half-input-line offsets are full output lines; no previous field is stored.
// out_sol must have the same phase as the line_double output.
module field_sync #(
    parameter integer H_SAMPLES = 1816,
    parameter integer VS_LINES = 5,
    parameter integer CW = $clog2(2*H_SAMPLES+1)
)(
    input wire clk, reset, field_start, out_sol,
    output reg vs_n,
    output reg frame_start
);
    reg [CW-1:0] delay_count;
    reg delay_active, pending;
    integer remaining;
    wire due = delay_active && delay_count == 0;
    always @(posedge clk) begin
        if (reset) begin
            delay_count <= 0; delay_active <= 0; pending <= 0;
            remaining <= 0; vs_n <= 1; frame_start <= 0;
        end else begin
            frame_start <= 0;
            if (field_start) begin
                delay_count <= 2*H_SAMPLES-1;
                delay_active <= 1;
            end else if (delay_active) begin
                if (delay_count != 0) delay_count <= delay_count - 1'b1;
                else begin delay_active <= 0; pending <= 1; end
            end
            if (out_sol) begin
                if (pending || due) begin
                    pending <= 0; remaining <= VS_LINES;
                    vs_n <= 0; frame_start <= 1;
                end else if (remaining > 1) remaining <= remaining - 1;
                else begin remaining <= 0; vs_n <= 1; end
            end
        end
    end
endmodule
