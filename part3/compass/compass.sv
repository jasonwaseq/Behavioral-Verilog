module compass
  (
    input logic [0:0]  clk_i,
    input logic [0:0]  reset_i,
    input logic [1:0]  direction_i,
    input logic [0:0]  valid_i,
    output logic [0:0] sequence_detected_o
   );

  typedef enum logic [1:0] {
    IDLE,
    S01,
    S11,
    S10
  } state_e;

  state_e state_r, state_n;

  always_comb begin
    state_n = state_r;
    sequence_detected_o = 1'b0;

    case (state_r) 
      IDLE : begin
        if (valid_i) begin
          if (direction_i == 2'b00)
          state_n = S11;
          else if (direction_i == 2'b01)
          state_n = S10;
          else if (direction_i == 2'b10)
          state_n = S01;
          else if (direction_i == 2'b11)
          state_n = S11;
        end
      end
      S01 : begin
        if (valid_i) begin
          if (direction_i == 2'b00)
          state_n = IDLE;
          else if (direction_i == 2'b01)
          state_n = S01;
          else if (direction_i == 2'b10) begin
          state_n = IDLE;
          sequence_detected_o = 1'b1;
          end
          else if (direction_i == 2'b11)
          state_n = S11;
        end
      end
      S11 : begin
        if (valid_i) begin
          if (direction_i == 2'b00) begin
          state_n = IDLE;
          sequence_detected_o = 1'b1;
          end
          else if (direction_i == 2'b01) begin
          state_n = S10;
          sequence_detected_o = 1'b1;
          end
          else if (direction_i == 2'b10) 
          state_n = S01;
          else if (direction_i == 2'b11)
          state_n = S11;
        end
      end
      S10 : begin
        if (valid_i) begin
          if (direction_i == 2'b00)
          state_n = IDLE;
          else if (direction_i == 2'b01)
          state_n = S01;
          else if (direction_i == 2'b10) begin
            state_n = IDLE;
            sequence_detected_o = 1'b1;
          end
          else if (direction_i == 2'b11)
          state_n = IDLE;
        end
      end
      default : state_n = IDLE;
    endcase
  end

  always_ff @(posedge clk_i) begin
    if (reset_i) 
      state_r <= IDLE;
    else
      state_r <= state_n;
  end


endmodule
