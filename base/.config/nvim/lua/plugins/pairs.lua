return {
  {
    "echasnovski/mini.pairs",
    enabled = false,
  },

  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    opts = {
      enable_check_bracket_line = false,
      ignored_next_char = "",
    },
    config = function(_, opts)
      local npairs = require("nvim-autopairs")
      npairs.setup(opts)

      local Rule = require("nvim-autopairs.rule")
      local cond = require("nvim-autopairs.conds")

      npairs.add_rules({
        Rule(" ", " ")
            :with_pair(function(options)
              local pair = options.line:sub(options.col - 1, options.col)
              return vim.tbl_contains({ "()", "[]", "{}" }, pair)
            end),
      })
    end,
  },
}
