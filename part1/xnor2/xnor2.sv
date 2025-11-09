module xnor2
  (input [0:0] a_i
  ,input [0:0] b_i
  ,output [0:0] c_o);

   // For Lab 2, you may use assign statements!
   // Your code here:

  logic [0:0] c_l;

  always_comb begin
    c_l = 1'b0;
    if (a_i == b_i) begin
      c_l = 1'b1; 
    end
  end

  assign c_o = c_l;

endmodule
