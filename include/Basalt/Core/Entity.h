#pragma once

#include <cstdint>
#include <limits>

namespace Basalt
{
    struct Entity final
    {
        static constexpr std::uint32_t InvalidIndex = std::numeric_limits<std::uint32_t>::max();

        std::uint32_t Index = InvalidIndex;
        std::uint32_t Generation = 0;

        [[nodiscard]] constexpr bool IsValid() const noexcept
        {
            return Index != InvalidIndex && Generation != 0;
        }

        friend constexpr bool operator==(const Entity&, const Entity&) noexcept = default;
    };
}
