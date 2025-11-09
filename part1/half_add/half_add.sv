module half_add
  (input [0:0] a_i
  ,input [0:0] b_i
  ,output [0:0] carry_o
  ,output [0:0] sum_o);

  logic [0:0] carry_l;
  logic [0:0] sum_l;

  always_comb begin
    sum_l = a_i ^ b_i;
    carry_l = a_i & b_i;
  end

  assign carry_o = carry_l;
  assign sum_o= sum_l;

endmodule
