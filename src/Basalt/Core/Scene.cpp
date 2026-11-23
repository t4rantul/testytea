#include <Basalt/Core/Scene.h>

#include <limits>
#include <stdexcept>
#include <utility>

namespace Basalt
{
    Entity Scene::AllocateEntity()
    {
        if (!FreeIndices.empty())
        {
            const std::uint32_t index = FreeIndices.back();
            FreeIndices.pop_back();
            Slot& slot = Slots[index];
            slot.Alive = true;
            ++AliveCount;
            return Entity{index, slot.Generation};
        }

        if (Slots.size() >= static_cast<std::size_t>(Entity::InvalidIndex))
        {
            throw std::length_error("Scene has exhausted its entity index space.");
        }

        const auto index = static_cast<std::uint32_t>(Slots.size());
        Slots.push_back(Slot{});
        Slots.back().Alive = true;
        ++AliveCount;
        return Entity{index, Slots.back().Generation};
    }

    Entity Scene::CreateEntity(std::string name)
    {
        const Entity entity = AllocateEntity();
        try
        {
            AddComponent<Transform>(entity);
            if (!name.empty())
            {
                AddComponent<Name>(entity, Name{std::move(name)});
            }
        }
        catch (...)
        {
            (void)DestroyEntity(entity);
            throw;
        }
        return entity;
    }

    bool Scene::DestroyEntity(Entity entity)
    {
        if (!IsAlive(entity))
        {
            return false;
        }

        for (auto& [type, pool] : Pools)
        {
            (void)type;
            (void)pool->Remove(entity.Index);
        }

        Slot& slot = Slots[entity.Index];
        slot.Alive = false;
        ++slot.Generation;
        if (slot.Generation == 0U)
        {
            slot.Generation = 1U;
        }
        --AliveCount;
        FreeIndices.push_back(entity.Index);
        return true;
    }

    bool Scene::IsAlive(Entity entity) const noexcept
    {
        return entity.IsValid() && entity.Index < Slots.size() && Slots[entity.Index].Alive &&
               Slots[entity.Index].Generation == entity.Generation;
    }

    std::size_t Scene::EntityCount() const noexcept
    {
        return AliveCount;
    }
}
