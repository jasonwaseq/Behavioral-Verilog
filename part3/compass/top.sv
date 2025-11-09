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
   // SPI Interface (Renamed via: https://www.oshwa.org/a-resolution-to-redefine-spi-signal-names/)
  ,output [0:0] spi_cs_o
  ,output [0:0] spi_sd_o
  ,input [0:0] spi_sd_i
  ,output [0:0] spi_sck_o
  ,output [5:1] led_o);

   wire [39:0] data_o;
   wire [39:0] data_i;
   wire [9:0]  position_x;
   wire [9:0]  position_y;

   wire [23:0] color_rgb;
   
  
   wire [0:0] reset_sync_r;
   wire [0:0] reset_r; // Use this as your reset_signal

   wire [3:1] button_sync_r;
   wire [3:1] button_r;

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
       
   generate
     for(genvar idx = 1; idx <= 3; idx++) begin
         dff
           #()
         sync_a
           (.clk_i(clk_12mhz_i)
           ,.reset_i(1'b0)
           ,.en_i(1'b1)
           ,.d_i(button_async_unsafe_i[idx])
           ,.q_o(button_sync_r[idx]));

         dff
           #()
         sync_b
           (.clk_i(clk_12mhz_i)
           ,.reset_i(1'b0)
           ,.en_i(1'b1)
           ,.d_i(button_sync_r[idx])
           ,.q_o(button_r[idx]));
     end
   endgenerate

   PmodJSTK
     #()
   jstk_i
     (.clk_12mhz_i(clk_12mhz_i)
     ,.reset_i(reset_r)
     ,.data_i(data_i)
     ,.spi_sd_i(spi_sd_i)
     ,.spi_cs_o(spi_cs_o)
     ,.spi_sck_o(spi_sck_o)
     ,.spi_sd_o(spi_sd_o)
     ,.data_o(data_o));

   assign position_y = {data_o[25:24], data_o[39:32]};
   assign position_x = {data_o[9:8], data_o[23:16]};

   assign data_i = {8'b10000100, color_rgb, 8'b00000000};

   // Red
   assign color_rgb[23:16] = 8'hff;
   // Green
   assign color_rgb[15:8] = 8'h00;
   // Blue
   assign color_rgb[7:0] = 8'h00;

   logic [1:0] left_r, right_r, up_r, down_r;
   assign left_r  = (position_x > 10'd640);
   assign right_r = (position_x < 10'd384);
   assign down_r  = (position_y < 10'd384);
   assign up_r    = (position_y > 10'd640); 

   logic [1:0] direction_next;
   logic [1:0] direction_r;
   always_comb begin
      direction_next = direction_r;
      if (reset_r)
         direction_next = 2'b00;
      else if (left_r && button_r[1])
         direction_next = 2'b10;
      else if (right_r && button_r[1])
         direction_next = 2'b01;
      else if (up_r && button_r[1])
         direction_next = 2'b00;
      else if (down_r && button_r[1])
         direction_next = 2'b11;
   end

   always_ff @(posedge clk_12mhz_i) begin
      if (reset_r)
         direction_r <= 2'b00;
      else
         direction_r <= direction_next;
   end
   
   wire button_ed;
   wire unbutton_ed;
   detect_edge
   detect_edge_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .button_i(button_r[1]),
    .button_o(button_ed),
    .unbutton_o(unbutton_ed)
   );
   
   logic seq_detected;
   compass compass_inst (
    .clk_i(clk_12mhz_i),
    .reset_i(reset_r),
    .direction_i(direction_r),
    .valid_i(button_ed),
    .sequence_detected_o(seq_detected)
   );
   
   wire [24:0] counter_w;
   counter
   #(.width_p(25)) 
   counter_inst (
   .clk_i(clk_12mhz_i),
   .reset_i(seq_detected),
   .up_i(1'b1 && (25'd12000000 > counter_w)),
   .down_i(1'b0),
   .count_o(counter_w)
   );

   wire win;
   assign win = (25'd12000000 > counter_w);

   assign led_o[5] = left_r;
   assign led_o[4] = right_r;
   assign led_o[3] = down_r;
   assign led_o[2] = up_r;
   assign led_o[1] = win;

endmodule