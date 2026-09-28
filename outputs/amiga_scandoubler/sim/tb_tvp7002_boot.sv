`timescale 1ns/1ps
module tb_tvp7002_boot;
    parameter integer N=1816, HALF=6, ALC_WAIT=20;
    reg clk=0,reset=1,power_good=0,video_locked=0;
    always #5 clk=~clk;
    wire adc_reset_n,adc_pwdn,scl_low,sda_low,qualified_ref,video_allowed,fault;
    wire [2:0] write_error;
    wire [7:0] failed_register;
    tri1 scl,sda;
    reg slave_low=0,stuck=0;
    assign scl=scl_low?1'b0:1'bz;
    assign sda=sda_low||slave_low||stuck?1'b0:1'bz;
    tvp7002_boot #(.H_SAMPLES(N),.HALF_CYCLES(HALF),.TIMEOUT_CYCLES(20*HALF),
      .POWER_WAIT_CYCLES(10),.RESET_CYCLES(5),.SETTLE_CYCLES(8),.ALC_WAIT_CYCLES(ALC_WAIT)) dut
      (.clk(clk),.reset(reset),.power_good(power_good),.video_locked(video_locked),
       .scl_in(scl),.sda_in(sda),.adc_reset_n(adc_reset_n),.adc_pwdn(adc_pwdn),
       .scl_low(scl_low),.sda_low(sda_low),.qualified_ref(qualified_ref),
       .video_allowed(video_allowed),.fault(fault),.write_error(write_error),.failed_register(failed_register));
    integer phase=0,bytes=0,starts=0,stops=0,nack_transaction=-1,cycle=0,last_stop=0,checks=0;
    reg active=0;
    reg [7:0] shift=0,received[0:3];
    reg [15:0] expected[0:35];
    always @(posedge clk)cycle=cycle+1;
    always @(negedge adc_reset_n) begin slave_low=0;active=0;end
    always @(negedge sda) begin
        #1;
        if(scl && !reset && adc_reset_n) begin
            if(adc_pwdn) $fatal(1,"I2C while powered down");
            active=1;phase=0;bytes=0;starts=starts+1;
        end
    end
    always @(posedge scl) begin
        #1;
        if(active && adc_reset_n) begin
            if(phase<8) begin shift={shift[6:0],sda};phase=phase+1;
                if(phase==8) received[bytes]=shift;
            end else phase=9;
        end
    end
    always @(negedge scl) begin
        #1;
        if(active && adc_reset_n) begin
            if(phase==8)slave_low=!(starts-1==nack_transaction && bytes==2);
            else if(phase==9)begin slave_low=0;phase=0;bytes=bytes+1;end
        end else slave_low=0;
    end
    always @(posedge sda) begin
        #1;
        if(scl && active && !reset && adc_reset_n) begin
            active=0;
            if(bytes!=3 || received[0]!==8'hb8 ||
               {received[1],received[2]}!==expected[starts-1])
                $fatal(1,"Wire sequence mismatch index=%0d got=%h/%h/%h",starts-1,received[0],received[1],received[2]);
            stops=stops+1;last_stop=cycle;checks=checks+1;
        end
    end
    task tick(input integer n);repeat(n)@(negedge clk);endtask
    task restart;
        begin
            @(negedge clk);reset=1;power_good=0;video_locked=0;stuck=0;slave_low=0;active=0;
            tick(8);reset=0;starts=0;stops=0;nack_transaction=-1;
            tick(30);
            if(starts || qualified_ref || adc_reset_n || !adc_pwdn) $fatal(1,"Startup not inhibited");
            power_good=1;
        end
    endtask
    task finish(input integer want_fault);
        integer n;
        begin
            n=0;
            while(!qualified_ref && !fault && n<10000*HALF+ALC_WAIT+500)begin tick(1);n=n+1;end
            if(want_fault) begin
                if(!fault || qualified_ref || video_allowed) $fatal(1,"Missing failure inhibition");
            end else begin
                if(!qualified_ref || fault || stops!=36 || cycle-last_stop<ALC_WAIT)
                    $fatal(1,"Configuration incomplete or ALC wait too short");
                if(video_allowed) $fatal(1,"Video enabled without video lock");
            end
        end
    endtask
    integer i,old_starts;
    initial begin
        expected[0]=16'h1703;expected[1]=16'h1900;expected[2]=16'h1aca;expected[3]=16'h0e12;
        expected[4]=16'h0f2e;expected[5]=16'h1058;expected[6]=16'h1500;expected[7]=16'h1800;
        case(N)
          1816:begin expected[8]=16'h0171;expected[9]=16'h0280;end
          1820:begin expected[8]=16'h0171;expected[9]=16'h02c0;end
          2048:begin expected[8]=16'h0180;expected[9]=16'h0200;end
          default:$fatal(1,"No independent expected divider profile");
        endcase
        expected[10]=16'h0310;expected[11]=16'h0400;expected[12]=16'h0506;expected[13]=16'h0610;
        expected[14]=16'h0780;expected[15]=16'h210d;expected[16]=16'h2204;expected[17]=16'h3602;
        expected[18]=16'h1b88;expected[19]=16'h1c08;expected[20]=16'h0819;expected[21]=16'h0919;
        expected[22]=16'h0a19;expected[23]=16'h0b80;expected[24]=16'h0c80;expected[25]=16'h0d80;
        expected[26]=16'h1d00;expected[27]=16'h1e10;expected[28]=16'h1f10;expected[29]=16'h2010;
        expected[30]=16'h2680;expected[31]=16'h2833;expected[32]=16'h2a07;expected[33]=16'h2d00;
        expected[34]=16'h3118;expected[35]=16'h1702;
        restart();finish(0);video_locked=1;tick(5);
        if(!video_allowed || !qualified_ref) $fatal(1,"Lock acquisition dependency");
        old_starts=starts;video_locked=0;tick(50);
        if(video_allowed || !qualified_ref || starts!=old_starts) $fatal(1,"Lock loss triggers wrong config behavior");
        power_good=0;tick(10);starts=0;stops=0;power_good=1;finish(0);
        if(HALF==6) begin
            for(i=0;i<36;i=i+1) begin
                restart();nack_transaction=i;finish(1);tick(20);
                if(write_error!=3 || failed_register!==expected[i][15:8] || starts!=i+1 ||
                   adc_reset_n || !adc_pwdn) $fatal(1,"NACK handling index=%0d",i);
                old_starts=starts;tick(100);if(starts!=old_starts) $fatal(1,"Unexpected retry");
            end
            restart();stuck=1;finish(1);tick(20);
            if(write_error!=4 || failed_register!=8'h17 || scl_low || sda_low)
                $fatal(1,"Stuck bus handling failed");
            restart();wait(starts==5);power_good=0;tick(20);
            if(qualified_ref || adc_reset_n || !adc_pwdn || scl_low || sda_low)
                $fatal(1,"Power loss mid-write not handled");
            starts=0;stops=0;power_good=1;finish(0);
        end
        $display("PASS tvp7002_boot N=%0d HALF=%0d ALC_WAIT=%0d: %0d complete wire transactions; divider order, config retention, video-lock gating, power restart%s",N,HALF,ALC_WAIT,checks,HALF==6?", all 36 data-NACK positions, stuck bus, mid-write power loss":"");
        $finish;
    end
    initial begin #200000000;$fatal(1,"Timeout");end
endmodule
