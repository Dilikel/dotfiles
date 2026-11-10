return {
  {
    "saghen/blink.cmp",
    opts = {
      completion = {
        accept = {
          auto_brackets = { enabled = false },
        },
      },
    },
  },

  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        ["*"] = {
          capabilities = {
            textDocument = {
              completion = {
                completionItem = {
                  snippetSupport = false,
                },
              },
            },
          },
        },
        gopls = {
          settings = {
            gopls = {
              usePlaceholders = false,
            },
          },
        },
      },
    },
  },
}
