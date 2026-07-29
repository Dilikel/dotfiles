return {
  "nvim-neo-tree/neo-tree.nvim",
  opts = {
    sort_function = function(a, b)
      if a.name == nil then
        return false
      end
      if b.name == nil then
        return false
      end

      if a.type ~= b.type then
        return a.type == "directory"
      end

      local function natural_cmp(ax, ay)
        local i, j = 1, 1
        while i <= #ax and j <= #ay do
          local sx, ex = ax:find("%d+", i)
          local sy, ey = ay:find("%d+", j)

          local cx = sx and ax:sub(i, sx - 1) or ax:sub(i)
          local cy = sy and ay:sub(j, sy - 1) or ay:sub(j)

          if cx ~= cy then
            return cx < cy
          end

          if sx and sy then
            local nx = tonumber(ax:sub(sx, ex))
            local ny = tonumber(ay:sub(sy, ey))
            if nx ~= ny then
              return nx < ny
            end
            i, j = ex + 1, ey + 1
          else
            return #ax < #ay
          end
        end
        return #ax < #ay
      end

      return natural_cmp(a.name, b.name)
    end,
  },
}
