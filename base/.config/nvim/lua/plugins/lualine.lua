return {
  "nvim-lualine/lualine.nvim",
  opts = function(_, opts)
    local function line_char_count()
      local line = vim.api.nvim_get_current_line()
      local count = vim.str_utfindex(line)
      return "count: " .. count
    end

    table.insert(opts.sections.lualine_x, 1, {
      line_char_count,
      color = { fg = "#ff9e64" },
    })
  end,
}
