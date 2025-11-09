// Top-level design file for the icebreaker FPGA board
module top
  (input [0:0] clk_12mhz_i
  ,input [0:0] reset_n_async_unsafe_i
   // n: Negative Polarity (0 when pressed, 1 otherwise)
   // async: Not synchronized to clock
   // unsafe: Not De-Bounced
  ,input [3:1] button_async_unsafe_i
   // async: Not synchronized to clock
   // unsafe: Not De-Bounced
  ,output [7:0] ssd_o
  ,output [5:1] led_o);

   // For this demonstration, instantiate your Counter modules to
   // drive the output wires of ssd_o. You may only use structural
   // verilog, the modules in provided_modules, and your lfsr module,
   // and your counter.
   // 
   // Hint: A 12 MHz clock is _very fast_ for human consumption. You
   // should use your counter to slow down your LFSR by generating a
   // new clock. In our solution, about 22 bits is sufficent.

   // These two D Flip Flops form what is known as a Synchronizer. We
   // will learn about these in Week 5, but you can see more here:
   // https://inst.eecs.berkeley.edu/~cs150/sp12/agenda/lec/lec16-synch.pdf
   wire [0:0] reset_n_sync_r;
   wire [0:0] reset_sync_r;
   wire [0:0] reset_r; // Use this as your reset_signal
   dff
     #()
   sync_a
     (.clk_i(clk_12mhz_i)
     ,.reset_i(1'b0)
     ,.en_i(1'b1)
     ,.d_i(reset_n_async_unsafe_i)
     ,.q_o(reset_n_sync_r));

   inv
     #()
   inv
     (.a_i(reset_n_sync_r)
     ,.b_o(reset_sync_r));

   dff
     #()
   sync_b
     (.clk_i(clk_12mhz_i)
     ,.reset_i(1'b0)
     ,.en_i(1'b1)
     ,.d_i(reset_sync_r)
     ,.q_o(reset_r));
       
  // Your code goes here

  wire [21:0] time_count_w;

  counter
    #(.width_p(22))
  counter_time_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .up_i(1'b1),
    .down_i(1'b0),
    .count_o(time_count_w)
  );

  wire [0:0] button1_w;
  assign button1_w = button_async_unsafe_i[1];
  wire [0:0] button2_w;
  assign button2_w = button_async_unsafe_i[2];

  wire [0:0] button1_db;

  debounce
    #(.min_delay_p(4))
  debounce_button1_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .button_i(button1_w),
    .button_o(button1_db)
  );

  wire [0:0] button2_db;
  
  debounce
    #(.min_delay_p(4))
  debounce_button2_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .button_i(button2_w),
    .button_o(button2_db)
  );

  wire [0:0] button1_edge;
  wire [0:0] button1_unedge;

  detect_edge
    #()
  detect_button1edge_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .button_i(button1_db),
    .button_o(button1_edge),
    .unbutton_o(button1_unedge)
  );

  wire [0:0] button2_edge;
  wire [0:0] button2_unedge;

  detect_edge
    #()
  detect_button2edge_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .button_i(button2_db),
    .button_o(button2_edge),
    .unbutton_o(button2_unedge)
  );

  wire [7:0] count_w;
  
  counter
    #(.width_p(8))
  counter_count_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .up_i(button1_edge),
    .down_i(button2_edge),
    .count_o(count_w)
  );

  wire [7:0] top8_w;
  assign top8_w = count_w[7:0];
  wire [3:0] tophex_w;
  assign tophex_w = top8_w[7:4];
  wire [3:0] bottomhex_w;
  assign bottomhex_w = top8_w[3:0];

  wire [6:0] topssd_w;
  wire [6:0] bottomssd_w;

  hex2ssd
    #()
  hex2ssd_top_inst (
    .hex_i(tophex_w),
    .ssd_o(topssd_w)
  );

  hex2ssd
    #()
  hex2ssd_bottom_inst (
    .hex_i(bottomhex_w),
    .ssd_o(bottomssd_w)
  );

  wire [13:0] digit_count_w;

  counter
    #(.width_p(14))
  counter_digit_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .up_i(1'b1),
    .down_i(1'b0),
    .count_o(digit_count_w)
  );

  wire [0:0] digit_w;
  assign digit_w = digit_count_w[13];

  wire [6:0] ssd_w;

  genvar i;
  generate
    for (i = 0; i < 7; i++) begin : mux
      mux2 
        #()
      mux2_inst (
        .a_i(bottomssd_w[i]),   
        .b_i(topssd_w[i]),      
        .select_i(~digit_w),         
        .c_o(ssd_w[i])         
      );
    end
  endgenerate

  assign ssd_o = {digit_w, ssd_w}; 

  assign led_o = {time_count_w[21], button1_db, digit_count_w[13], button1_unedge, reset_r};

endmodule