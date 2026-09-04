return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        autotools_ls = {},
      },
    },
  },

  {
    "mfussenegger/nvim-lint",
    opts = {
      linters_by_ft = {
        make = { "checkmake" },
      },
    },
  },
}
