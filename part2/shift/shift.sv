module shift
  #(parameter width_p = 5
    /* verilator lint_off WIDTHTRUNC */
   ,parameter [width_p-1:0] reset_val_p = '0)
   /* verilator lint_on WIDTHTRUNC */   
   (input [0:0] clk_i
   ,input [0:0] reset_i
   ,input [0:0] enable_i
   ,input [0:0] d_i
   ,input [0:0] load_i
   ,input [width_p-1:0] data_i
   ,output [width_p-1:0] data_o);

  logic [width_p-1:0] data_l;

  always_ff @(posedge clk_i) begin
    if (reset_i)
      data_l <= reset_val_p;
    else if (load_i)
      data_l <= data_i;
    else if (enable_i) 
      data_l <= {data_l[width_p-2:0], d_i};
    else
      data_l <= data_l;
  end

  assign data_o = data_l;
     

endmodule
