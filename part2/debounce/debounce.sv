module debounce
  #(parameter min_delay_p = 4
    )
   (input [0:0] clk_i
   ,input [0:0] reset_i
   ,input [0:0] button_i
   ,output [0:0] button_o);

   // Your code here:

  wire [$clog2(min_delay_p):0] count_l;

  counter_sat
    #(.width_p($clog2(min_delay_p)+1),
      .reset_val_p(0),
      .sat_val_p(min_delay_p)
    )
  counter_sat_inst (
    .clk_i(clk_i),
    .reset_i(reset_i),
    .up_i(button_i),
    .down_i(~button_i),
    .count_o(count_l)
  );

  assign button_o = (count_l == (($clog2(min_delay_p)+1)'(min_delay_p)));
   
endmodule
