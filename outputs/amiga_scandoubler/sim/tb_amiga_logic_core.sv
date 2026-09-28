`timescale 1ns/1ps
module tb_amiga_logic_core;
    localparam N=1536,FL=625;
    reg clk_ref=0,adc_base=0,video_base=0,reset=0,power_good=0,pll_lock=0;
    reg outputs_enabled=0,stop_adc=0,nack_address=0;
    wire adc_clock=outputs_enabled && !stop_adc?adc_base:1'b0;
    wire video_clock=pll_lock?video_base:1'b0;
    reg [23:0] adc_rgb=0,source_color=24'habcdef;
    reg adc_hs_n=1,adc_vs_n=1;
    wire adc_reset_n,adc_pwdn,scl_low,sda_low,pll_reset;
    wire [23:0] dac_rgb;
    wire dac_blank_n,dac_psave_n,hs_out_n,vs_out_n,configured_ref,video_ready_ref,configuration_fault;
    wire [2:0] write_error,clock_fault_history,sync_fault_history;
    wire [7:0] failed_register;
    tri1 scl,sda;
    reg slave_low=0;
    assign scl=scl_low?1'b0:1'bz;
    assign sda=sda_low||slave_low?1'b0:1'bz;
    always #18.5 clk_ref=~clk_ref;
    always #18 adc_base=~adc_base;
    // 180 degrees of the 18 ns video period; ADC rising edges are 18+36k ns.
    initial begin #9;forever begin video_base=1;#9;video_base=0;#9;end end
    amiga_logic_core #(.H_SAMPLES(N),.VS_ALIGN_CYCLES(31),.HS_WIDTH(4),
      .X_START(6),.X_END(N-4),.Y_START(8),.Y_END(617),
      .I2C_HALF(6),.I2C_TIMEOUT(120),.POWER_WAIT(10),.ADC_RESET_HOLD(5),.ADC_SETTLE(8),.ALC_WAIT(20),
      .PLL_GOOD(3),.PLL_RESET_HOLD(10),.PLL_TIMEOUT(800)) dut
      (.clk_ref(clk_ref),.reset(reset),.power_good(power_good),.adc_clock(adc_clock),
       .video_clock(video_clock),.pll_lock(pll_lock),.adc_rgb(adc_rgb),.adc_hs_n(adc_hs_n),.adc_vs_n(adc_vs_n),
       .scl_in(scl),.sda_in(sda),.adc_reset_n(adc_reset_n),.adc_pwdn(adc_pwdn),.scl_low(scl_low),.sda_low(sda_low),
       .pll_reset(pll_reset),.dac_rgb(dac_rgb),.dac_blank_n(dac_blank_n),.dac_psave_n(dac_psave_n),
       .hs_out_n(hs_out_n),.vs_out_n(vs_out_n),.configured_ref(configured_ref),.video_ready_ref(video_ready_ref),
       .configuration_fault(configuration_fault),.write_error(write_error),.clock_fault_history(clock_fault_history),
       .sync_fault_history(sync_fault_history),.failed_register(failed_register));
    integer lock_count=0,sample_id=0,pixel_checks=0,phase=0,bytes=0,transactions=0;
    reg active=0;
    reg [7:0] shift=0,received[0:3];
    always @(negedge clk_ref)begin
        if(pll_reset)begin pll_lock=0;lock_count=0;end
        else if(lock_count==8)pll_lock=1;
        else lock_count=lock_count+1;
    end
    always @(negedge adc_reset_n)begin outputs_enabled=0;sample_id=0;slave_low=0;active=0;end
    always @(posedge adc_clock)begin
        #1.5;adc_rgb=source_color;adc_hs_n=sample_id%N>=128;
        adc_vs_n=sample_id%(N*FL/2)>=3*N;sample_id=sample_id+1;
    end
    always @(negedge sda)begin
        #1;if(scl && adc_reset_n && !reset)begin active=1;phase=0;bytes=0;end
    end
    always @(posedge scl)begin
        #1;if(active)begin
            if(phase<8)begin shift={shift[6:0],sda};phase=phase+1;if(phase==8)received[bytes]=shift;end
            else phase=9;
        end
    end
    always @(negedge scl)begin
        #1;if(active)begin
            if(phase==8)slave_low=!(nack_address && bytes==0);
            else if(phase==9)begin slave_low=0;phase=0;bytes=bytes+1;end
        end else slave_low=0;
    end
    always @(posedge sda)begin
        #1;if(scl && active && !reset && adc_reset_n)begin
            active=0;
            if(received[0]!==8'hb8) $fatal(1,"Wrong ADC address");
            if(!nack_address)begin
                if(bytes!=3) $fatal(1,"Incomplete startup write");
                if(transactions==0 && {received[1],received[2]}!==16'h1703) $fatal(1,"Missing initial output disable");
                if({received[1],received[2]}==16'h1702)begin
                    if(transactions!=35) $fatal(1,"ADC enabled prematurely");
                    outputs_enabled=1;
                end
                transactions=transactions+1;
            end
        end
    end
    always @(posedge video_clock)begin
        #1;if(dac_blank_n)begin
            if(dac_rgb!==source_color || !dac_psave_n || configuration_fault) $fatal(1,"End-to-end RGB mismatch");
            pixel_checks=pixel_checks+1;
        end else if(dac_rgb!==0) $fatal(1,"Unblanked RGB");
    end
    task ticks(input integer n);repeat(n)begin @(posedge clk_ref);#2;end endtask
    task active_video;
        integer n;
        begin
            n=0;while(!dac_blank_n && n<2000000)begin ticks(1);n=n+1;end
            if(!dac_blank_n || !video_ready_ref || transactions!=36) $fatal(1,"Whole-chain startup failed cfg=%b ready=%b tx=%0d pllreset=%b lock=%b clockfault=%b syncfault=%b",configured_ref,video_ready_ref,transactions,pll_reset,pll_lock,clock_fault_history,sync_fault_history);
        end
    endtask
    task dark;
        if(dac_blank_n || dac_rgb!==0 || dac_psave_n || !hs_out_n || !vs_out_n) $fatal(1,"Stopped chain output not suppressed");
    endtask
    initial begin
        // Apply an actual reset assertion while ADC/PLL clocks are stopped.
        // An initial declaration value alone is not a power-on-reset pulse.
        #1;reset=1;ticks(5);reset=0;ticks(20);power_good=1;active_video();ticks(3000);
        stop_adc=1;ticks(180);dark();
        source_color=24'h123456;stop_adc=0;active_video();ticks(3000);
        if(pixel_checks<5000) $fatal(1,"Too few end-to-end pixels");
        power_good=0;ticks(20);dark();
        transactions=0;nack_address=1;power_good=1;ticks(10000);
        if(!configuration_fault || write_error!=1 || failed_register!=8'h17) $fatal(1,"Boot NACK not propagated");
        dark();
        $display("PASS amiga_logic_core: %0d visible RGB checks; 36-write ADC start, input capture, clock/sync acquisition, stopped ADC recovery with new color, power loss and startup NACK",pixel_checks);
        $finish;
    end
    initial begin #200000000;$fatal(1,"Timeout");end
endmodule
