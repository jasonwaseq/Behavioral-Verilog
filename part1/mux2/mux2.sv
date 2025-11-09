module mux2
  (input [0:0] a_i
  ,input [0:0] b_i
  ,input [0:0] select_i
  ,output [0:0] c_o);

   // For Lab 2, you may use assign statements!
   // Your code here:

  logic [0:0] c_l;

  always_comb begin
    c_l = a_i;
    if (select_i) begin
    c_l = b_i;
    end
  end

  assign c_o = c_l;

endmodule
