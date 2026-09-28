`timescale 1ns/1ps
module tb_i2c_register_write;
    parameter integer HALF=6;
    reg clk=0,reset=1,start=0;
    always #5 clk=~clk;
    reg [6:0] address=7'h5c;
    reg [7:0] register_address=8'h15,write_data=8'h04;
    wire scl_low,sda_low,busy,done;
    wire [2:0] error;
    tri1 scl,sda;
    reg slave_low=0,stretch=0,stuck_sda=0;
    assign scl=scl_low||stretch?1'b0:1'bz;
    assign sda=sda_low||slave_low||stuck_sda?1'b0:1'bz;
    i2c_register_write #(.HALF_CYCLES(HALF),.TIMEOUT_CYCLES(20*HALF)) dut
      (.clk(clk),.reset(reset),.start(start),.address(address),
       .register_address(register_address),.write_data(write_data),
       .scl_in(scl),.sda_in(sda),.scl_low(scl_low),.sda_low(sda_low),
       .busy(busy),.done(done),.error(error));
    integer phase=0,byte_count=0,starts=0,stops=0,nack_at=-1;
    reg active=0;
    reg [7:0] shift=0;
    reg [7:0] received[0:3];
    // Slave observes only physical I2C pins, not DUT state or counters.
    always @(negedge sda) begin
        #1;
        if (scl && !reset) begin active=1;phase=0;byte_count=0;starts=starts+1;end
    end
    always @(posedge sda) begin
        #1;
        if (scl && !reset && active) begin active=0;stops=stops+1;end
    end
    always @(posedge scl) begin
        #1;
        if (active && !reset) begin
            if (phase<8) begin
                shift={shift[6:0],sda}; phase=phase+1;
                if (phase==8) received[byte_count]=shift;
            end else phase=9;
        end
    end
    always @(negedge scl) begin
        #1;
        if (active && !reset) begin
            if (phase==8) slave_low=(byte_count!=nack_at);
            else if (phase==9) begin slave_low=0;phase=0;byte_count=byte_count+1;end
        end else slave_low=0;
    end
    task restart;
      begin
        @(negedge clk);reset=1;start=0;stretch=0;stuck_sda=0;slave_low=0;active=0;
        repeat(5) @(negedge clk);
        reset=0;starts=0;stops=0;byte_count=0;nack_at=-1;
        address=7'h5c;register_address=8'h15;write_data=8'h04;
        repeat(5) @(negedge clk);
      end
    endtask
    task launch;
      begin @(negedge clk);start=1;@(negedge clk);start=0;end
    endtask
    task finish(input integer expected_error);
      integer t;
      begin
        t=0;
        while(!done && t<200*HALF+400) begin @(negedge clk);t=t+1;end
        if(t==200*HALF+400 || error!==expected_error || busy || scl_low || sda_low)
          $fatal(1,"Bad completion error=%0d expected=%0d t=%0d",error,expected_error,t);
        @(negedge clk);
        if(done) $fatal(1,"done must be one cycle");
      end
    endtask
    integer i;
    initial begin
        restart();launch();finish(0);
        if(starts!=1 || stops!=1 || byte_count!=3 || received[0]!==8'hb8 ||
           received[1]!==8'h15 || received[2]!==8'h04) $fatal(1,"Wire transaction mismatch");
        $display("PASS I2C: 7-bit 0x5c produces B8 / 15 / 04 and STOP");
        restart();launch();
        repeat(20) @(negedge clk);
        address=0;register_address=0;write_data=0;start=1;
        @(negedge clk);start=0;
        finish(0);
        if(received[0]!==8'hb8 || received[1]!==8'h15 || received[2]!==8'h04 || starts!=1)
          $fatal(1,"Inputs not latched / busy command accepted");
        $display("PASS I2C: request latched and busy request ignored");
        for(i=0;i<3;i=i+1) begin
          restart();nack_at=i;launch();finish(i+1);
          if(stops!=1 || byte_count!=i+1) $fatal(1,"NACK failed to terminate transaction");
        end
        $display("PASS I2C: address, register and data NACK each terminate with STOP");
        restart();
        fork
          begin launch();finish(0);end
          begin @(negedge scl);#2;stretch=1;repeat(HALF+29) @(negedge clk);stretch=0;end
        join
        if(byte_count!=3 || received[2]!==8'h04) $fatal(1,"Stretch corrupted data");
        $display("PASS I2C: clock stretching preserves transaction");
        restart();stuck_sda=1;repeat(5) @(negedge clk);
        starts=0;active=0; // Ignore START caused by the external fault injection.
        launch();finish(4);
        if(starts!=0) $fatal(1,"Started on occupied bus");
        $display("PASS I2C: occupied bus times out without START");
        restart();
        fork
          begin launch();finish(4);end
          begin @(negedge scl);#2;stretch=1;end
        join
        $display("PASS I2C: stuck SCL times out and releases master pins");
        restart();launch();repeat(6*HALF) @(negedge clk);reset=1;
        repeat(2) @(negedge clk);
        if(busy || scl_low || sda_low) $fatal(1,"Reset did not release bus");
        restart();launch();finish(0);
        $display("PASS I2C: mid-transaction reset and fresh transaction");
        $finish;
    end
    initial begin #1000000;$fatal(1,"test watchdog");end
endmodule
