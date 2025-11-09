module adder
  #(parameter width_p = 5)
  // You must fill in the bit widths of a_i, b_i and sum_o. a_i and
  // b_i must be width_p bits.
  (input [width_p-1:0] a_i
  ,input [width_p-1:0] b_i
  ,output [width_p:0] sum_o);

   // For Lab 2, you may use assign statements!
   // Your code here

  logic [width_p:0] sum_l;
  
  always_comb begin
    sum_l = a_i + b_i;
  end

  assign sum_o = sum_l;

endmodule
