`timescale 1ns/1ps
// Fault assertion is asynchronous; release is synchronized locally to clk.
// Register pixel, blank and sync together; PSAVE remains independently guarded.
module dac_output_stage (
    input wire clk, reset, permit, valid,
    input wire [23:0] rgb_in,
    input wire blank_in, hs_in, vs_in,
    output reg [23:0] rgb,
    output reg blank_n, hs_n, vs_n
);
    // Configuration-time values also cover a clock that never starts.
    // Must be retained as device FF INIT values in the mapped implementation.
    initial begin rgb=0;blank_n=0;hs_n=1;vs_n=1;end
    wire clear_request=reset || !permit;
    (* ASYNC_REG="TRUE" *) reg [1:0] release_pipe=2'b11;
    always @(posedge clk or posedge clear_request)
        if(clear_request) release_pipe<=2'b11;
        else release_pipe<={release_pipe[0],1'b0};
    wire clear=release_pipe[1];
    always @(posedge clk or posedge clear) begin
        if (clear) begin
            rgb<=24'b0; blank_n<=1'b0; hs_n<=1'b1; vs_n<=1'b1;
        end else begin
            blank_n<=valid && blank_in;
            rgb<=(valid && blank_in)?rgb_in:24'b0;
            hs_n<=hs_in;
            vs_n<=vs_in;
        end
    end
endmodule
