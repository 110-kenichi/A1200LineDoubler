`timescale 1ns/1ps
module tb_supervised_video_core;
    reg clk_ref=0,clk_video=0,reset=1,qualified_ref=0,pll_lock=0,running=1;
    reg sample_ce=0,line_start=0,field_start=0;
    reg [23:0] pixel_in=24'habcdef;
    wire [23:0] rgb;
    wire blank_n,hs_n,vs_n,ready_ref,reset_video,protocol_error,dac_psave_n;
    integer t=0,active_pixels=0;
    reg [23:0] dac_latched=0;
    // Minimal synchronous DAC input-register model, not an analog DAC model.
    // Crucially, lowering BLANK with no CLOCK edge cannot update this register.
    always @(posedge clk_video) dac_latched<=blank_n?rgb:24'b0;
    always #18.5 clk_ref=~clk_ref;
    always begin #9;if(running) clk_video=~clk_video;end
    supervised_video_core #(.H_SAMPLES(32),.HS_WIDTH(4),.X_START(6),
      .X_END(28),.Y_START(8),.Y_END(30)) dut
      (.clk_ref(clk_ref),.clk_video(clk_video),.reset(reset),
       .qualified_ref(qualified_ref),.pll_lock(pll_lock),
       .sample_ce(sample_ce),.line_start(line_start),.field_start(field_start),
       .pixel_in(pixel_in),.rgb(rgb),.blank_n(blank_n),.hs_n(hs_n),.vs_n(vs_n),
       .ready_ref(ready_ref),.reset_video(reset_video),.protocol_error(protocol_error),.dac_psave_n(dac_psave_n));
    always @(negedge clk_video) begin
        if(reset_video) begin t=0;sample_ce=0;line_start=0;field_start=0;end
        else begin
            sample_ce=(t%2==0);line_start=(t%64==0);field_start=(t%1280==0);
            t=t+1;
        end
    end
    always @(posedge clk_video) begin
        #1;
        if(blank_n) begin
            if(rgb!==24'habcdef || protocol_error) $fatal(1,"Wrong active pixel");
            active_pixels=active_pixels+1;
        end
    end
    task active;
        integer n;
        begin
            n=0;
            while(!blank_n && n<10000) begin @(negedge clk_ref);n=n+1;end
            if(!blank_n) $fatal(1,"No active video");
        end
    endtask
    task dark;
        begin
            if(blank_n!==0 || rgb!==0 || hs_n!==1 || vs_n!==1 || reset_video!==1 || dac_psave_n!==0)
                $fatal(1,"Stopped clock FPGA output pins not blanked");
        end
    endtask
    initial begin
        #100;reset=0;qualified_ref=1;pll_lock=1;active();
        repeat(3000) @(negedge clk_video);
        active();
        @(posedge clk_video);#2;
        if(dac_latched!==24'habcdef) $fatal(1,"DAC model did not latch active pixel");
        // Freeze a nonzero active pixel. Blanking must work without another edge.
        running=0;repeat(85) @(negedge clk_ref);dark();
        if(dac_latched!==24'habcdef) $fatal(1,"DAC model incorrectly blanks without a clock edge");
        $display("CONFIRMED LIMITATION: DAC input register retains nonzero pixel after clock stops; digital BLANK alone is insufficient for analog muting");
        running=1;active();
        running=0;pll_lock=0;#1;dark();pll_lock=1;
        repeat(300) @(negedge clk_ref);dark();
        running=1;active();
        qualified_ref=0;#1;dark();qualified_ref=1;active();
        $display("PASS supervised_video_core: %0d active RGB checks; nonzero-pixel clock freeze, asynchronous blanking, lock/config loss and restart",active_pixels);
        $finish;
    end
    initial begin #2000000;$fatal(1,"Timeout");end
endmodule
