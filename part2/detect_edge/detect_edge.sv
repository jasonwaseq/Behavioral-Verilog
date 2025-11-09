module detect_edge
   (input [0:0] clk_i
    // reset_i will go low at least one cycle before a button is pushed.
   ,input [0:0] reset_i
   ,input [0:0] button_i
    // Should go high for 1 cycle, after a positive edge
   ,output [0:0] button_o
    // Should go high for 1 cycle, after a negative edge
   ,output [0:0] unbutton_o
   );

   // Your code here:

   logic [0:0] button_l;
   logic [0:0] unbutton_l;
   logic [0:0] prevbutton_l;

   always_ff @(posedge clk_i) begin
      if (reset_i) begin
         prevbutton_l <= 1'b0;
         button_l <= 1'b0;
         unbutton_l <= 1'b0;
      end
      else begin
         button_l <= (button_i && !prevbutton_l);
         unbutton_l <= (!button_i && prevbutton_l);
         prevbutton_l <= button_i;
      end
   end

   assign button_o = button_l;
   assign unbutton_o = unbutton_l;

endmodule
