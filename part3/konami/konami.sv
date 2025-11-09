module konami
   (input [0:0] clk_i
   ,input [0:0] reset_i
   ,input [0:0] up_i
   ,input [0:0] unup_i
   ,input [0:0] down_i
   ,input [0:0] undown_i
   ,input [0:0] left_i
   ,input [0:0] unleft_i
   ,input [0:0] right_i
   ,input [0:0] unright_i
   ,input [0:0] b_i
   ,input [0:0] unb_i
   ,input [0:0] a_i
   ,input [0:0] una_i
   ,input [0:0] start_i
   ,input [0:0] unstart_i
   ,output [0:0] cheat_code_unlocked_o);

    typedef enum logic [3:0] {
        IDLE,
        UP1, 
        UP2,
        DOWN1, 
        DOWN2,
        LEFT1, 
        RIGHT1,
        LEFT2, 
        RIGHT2,
        B, 
        A,
        START
    } state_e;

    state_e state_r, state_n;

    logic [0:0] up_press, down_press, left_press, right_press, b_press, a_press, start_press;

    logic [0:0] up_l, down_l, left_l, right_l, b_l, a_l, start_l;

    always_ff @(posedge clk_i or posedge reset_i) begin
        if (reset_i) begin
            up_press    <= 0;
            down_press  <= 0;
            left_press  <= 0;
            right_press <= 0;
            b_press     <= 0;
            a_press     <= 0;
            start_press <= 0;
            state_r     <= IDLE;
        end else begin
            if (up_i)    up_press    <= 1;
            if (down_i)  down_press  <= 1;
            if (left_i)  left_press  <= 1;
            if (right_i) right_press <= 1;
            if (b_i)     b_press     <= 1;
            if (a_i)     a_press     <= 1;
            if (start_i) start_press <= 1;

            if (unup_i)    up_press    <= 0;
            if (undown_i)  down_press  <= 0;
            if (unleft_i)  left_press  <= 0;
            if (unright_i) right_press <= 0;
            if (unb_i)     b_press     <= 0;
            if (una_i)     a_press     <= 0;
            if (unstart_i) start_press <= 0;

            state_r <= state_n;
        end
    end

    always_comb begin
        up_l    = up_press    && unup_i;
        down_l  = down_press  && undown_i;
        left_l  = left_press  && unleft_i;
        right_l = right_press && unright_i;
        b_l     = b_press     && unb_i;
        a_l     = a_press     && una_i;
        start_l = start_press && unstart_i;
    end

    always_comb begin
        state_n = state_r; 
        case (state_r)
            IDLE:   if (up_l) state_n = UP1;
            UP1:    if (up_l) state_n = UP2;
            UP2:    if (down_l) state_n = DOWN1;
            DOWN1:  if (down_l) state_n = DOWN2;
            DOWN2:  if (left_l) state_n = LEFT1;
            LEFT1:  if (right_l) state_n = RIGHT1;
            RIGHT1: if (left_l) state_n = LEFT2;
            LEFT2:  if (right_l) state_n = RIGHT2;
            RIGHT2: if (b_l) state_n = B;
            B:      if (a_l) state_n = A;
            A:      if (start_l) state_n = START;
            START: state_n = IDLE; 
            default: state_n = IDLE;
        endcase
    end

    assign cheat_code_unlocked_o = (state_r == START);

endmodule
