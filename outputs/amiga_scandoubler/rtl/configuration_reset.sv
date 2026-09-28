`timescale 1ns/1ps
// Candidate configuration-time reset. Requires implementation tool support for
// initialized registers/GSR; verify in fitted netlist before programming.
module configuration_reset #(parameter integer CYCLES=32)(
    input wire clk_ref, output wire reset
);
    reg [CYCLES-1:0] released = {CYCLES{1'b0}};
    initial if(CYCLES<2) $fatal(1,"Reset must span at least two reference clocks");
    always @(posedge clk_ref) released <= {released[CYCLES-2:0],1'b1};
    assign reset = !released[CYCLES-1];
endmodule
