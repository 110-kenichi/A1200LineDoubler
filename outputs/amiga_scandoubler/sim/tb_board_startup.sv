`timescale 1ns/1ps
// Interface stubs only. NOT Gowin primitive models and NOT PLL/ODDR validation.
module gowin_video_pll #(parameter INPUT_MHZ="28.375",parameter VCO_DIV=8)
 (input adc_clock,reset_pll,output video_clock,locked);
 assign video_clock=0; assign locked=0;
endmodule
module ODDR #(parameter TXCLK_POL=0,INIT=0)
 (input CLK,D0,D1,TX,output reg Q0=INIT,output Q1);
 assign Q1=TX;
 always @(posedge CLK) Q0<=D0;
 always @(negedge CLK) Q0<=D1;
endmodule
module tb_board_startup;
 reg clk=0; wire r2,r32,r65;
 configuration_reset #(.CYCLES(2)) a(clk,r2);
 configuration_reset #(.CYCLES(32)) b(clk,r32);
 configuration_reset #(.CYCLES(65)) c(clk,r65);
 tri1 scl,sda;
 wire rst,pwdn,dc,blank,psave,hs,vs;
 wire [7:0] r,g,bl;
 amiga_board_top #(.H_SAMPLES(1816),.VS_ALIGN_CYCLES(31),.HS_WIDTH(4),
   .X_START(6),.X_END(1812),.Y_START(8),.Y_END(617)) board
  (.REF_27M(clk),.POWER_GOOD(1'b0),.ADC_CLK(1'b0),.ADC_HS(1'b1),.ADC_VS(1'b1),
   .ADC_R(8'h12),.ADC_G(8'h34),.ADC_B(8'h56),.I2C_SCL(scl),.I2C_SDA(sda),
   .ADC_RESET_N(rst),.ADC_PWDN(pwdn),.DAC_R(r),.DAC_G(g),.DAC_B(bl),
   .DAC_CLK_RAW(dc),.DAC_BLANK_N(blank),.DAC_PSAVE_N(psave),.H_OUT_RAW(hs),.V_OUT_RAW(vs));
 integer i,checks=0;
 initial begin
   #100;
   if({r2,r32,r65}!==3'b111)$fatal(1,"Reset released without clock");
   for(i=1;i<=100;i=i+1)begin
     clk=1;#1;
     if(r2!==(i<2) || r32!==(i<32) || r65!==(i<65))$fatal(1,"Reset length %0d",i);
     if(i>=3 && ({rst,pwdn,blank,psave,hs,vs}!==6'b010011 || {r,g,bl}!==24'b0 || scl!==1'b1 || sda!==1'b1))
       $fatal(1,"Unsafe or unknown board outputs while power not good at %0d",i);
     checks=checks+1;#17;clk=0;#19;
     if(i==12)begin
       #1000;
       if({r2,r32,r65}!==3'b011)$fatal(1,"Reset advanced without reference clocks");
     end
   end
   $display("PASS board_startup: %0d reference edges; reset lengths 2/32/65; delayed/stopped reference; safe pins with ADC stopped and power low",checks);
   $display("Scope: behavioral initialization and board elaboration with stubs; NOT vendor PLL/ODDR or fitted reset validation");
   $finish;
 end
endmodule
