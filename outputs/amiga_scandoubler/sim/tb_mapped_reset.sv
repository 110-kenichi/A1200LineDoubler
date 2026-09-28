`timescale 1ns/1ps
module tb_mapped_reset;
 parameter integer CYCLES=32;
 reg clk=0; wire reset;
 configuration_reset dut(.clk_ref(clk),.reset(reset));
 integer i;
 initial begin
   #100;if(reset!==1'b1)$fatal(1,"Mapped reset missing at startup");
   for(i=1;i<=CYCLES+10;i=i+1)begin
     clk=1;#1;
     if(reset!==(i<CYCLES))$fatal(1,"Mapped reset release edge %0d",i);
     #17;clk=0;#19;
     if(i==1)begin
       #1000;if(reset!==1'b1)$fatal(1,"Mapped reset advanced while reference stopped");
     end
   end
   $display("PASS mapped_reset CYCLES=%0d: initial assertion, stopped reference, exact release edge",CYCLES);
   $finish;
 end
endmodule
