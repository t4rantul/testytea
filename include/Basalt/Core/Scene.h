#pragma once

#include <Basalt/Core/Entity.h>

#include <glm/gtc/quaternion.hpp>
#include <glm/vec3.hpp>

#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <typeindex>
#include <typeinfo>
#include <unordered_map>
#include <utility>
#include <vector>

namespace Basalt
{
    struct Transform final
    {
        glm::vec3 Position{0.0F};
        glm::quat Rotation{1.0F, 0.0F, 0.0F, 0.0F};
        glm::vec3 Scale{1.0F};
    };

    struct Name final
    {
        std::string Value;
    };

    // Scene is a main-thread object. Structural changes during ForEach of the same
    // component type are unsupported. Component pointers do not survive removal.
    class Scene final
    {
    public:
        Scene() = default;
        ~Scene() = default;
        Scene(const Scene&) = delete;
        Scene& operator=(const Scene&) = delete;
        Scene(Scene&&) = delete;
        Scene& operator=(Scene&&) = delete;

        [[nodiscard]] Entity CreateEntity(std::string name = {});
        [[nodiscard]] bool DestroyEntity(Entity entity);
        [[nodiscard]] bool IsAlive(Entity entity) const noexcept;
        [[nodiscard]] std::size_t EntityCount() const noexcept;

        template <typename T, typename... TArgs>
        T& AddComponent(Entity entity, TArgs&&... args)
        {
            if (!IsAlive(entity))
            {
                throw std::invalid_argument("Cannot add a component to an invalid or stale entity.");
            }
            return GetOrCreatePool<T>().Add(entity.Index, std::forward<TArgs>(args)...);
        }

        template <typename T>
        [[nodiscard]] T* GetComponent(Entity entity) noexcept
        {
            if (!IsAlive(entity))
            {
                return nullptr;
            }
            ComponentPool<T>* pool = FindPool<T>();
            return pool == nullptr ? nullptr : pool->Get(entity.Index);
        }

        template <typename T>
        [[nodiscard]] const T* GetComponent(Entity entity) const noexcept
        {
            if (!IsAlive(entity))
            {
                return nullptr;
            }
            const ComponentPool<T>* pool = FindPool<T>();
            return pool == nullptr ? nullptr : pool->Get(entity.Index);
        }

        template <typename T>
        [[nodiscard]] bool HasComponent(Entity entity) const noexcept
        {
            return GetComponent<T>(entity) != nullptr;
        }

        template <typename T>
        [[nodiscard]] bool RemoveComponent(Entity entity) noexcept
        {
            if (!IsAlive(entity))
            {
                return false;
            }
            ComponentPool<T>* pool = FindPool<T>();
            return pool != nullptr && pool->Remove(entity.Index);
        }

        template <typename T>
        [[nodiscard]] std::size_t ComponentCount() const noexcept
        {
            const ComponentPool<T>* pool = FindPool<T>();
            return pool == nullptr ? 0U : pool->Count();
        }

        template <typename T, typename TFunction>
        void ForEach(TFunction&& function)
        {
            ComponentPool<T>* pool = FindPool<T>();
            if (pool == nullptr)
            {
                return;
            }
            for (auto& [index, component] : pool->Items)
            {
                const Entity entity{index, Slots[index].Generation};
                std::invoke(function, entity, component);
            }
        }

    private:
        struct Slot final
        {
            std::uint32_t Generation = 1;
            bool Alive = false;
        };

        class IComponentPool
        {
        public:
            virtual ~IComponentPool() = default;
            virtual bool Remove(std::uint32_t index) noexcept = 0;
        };

        template <typename T>
        class ComponentPool final : public IComponentPool
        {
        public:
            template <typename... TArgs>
            T& Add(std::uint32_t index, TArgs&&... args)
            {
                auto [iterator, inserted] = Items.try_emplace(index, std::forward<TArgs>(args)...);
                if (!inserted)
                {
                    throw std::logic_error("Entity already has this component.");
                }
                return iterator->second;
            }

            [[nodiscard]] T* Get(std::uint32_t index) noexcept
            {
                auto iterator = Items.find(index);
                return iterator == Items.end() ? nullptr : &iterator->second;
            }

            [[nodiscard]] const T* Get(std::uint32_t index) const noexcept
            {
                auto iterator = Items.find(index);
                return iterator == Items.end() ? nullptr : &iterator->second;
            }

            bool Remove(std::uint32_t index) noexcept override
            {
                return Items.erase(index) != 0U;
            }

            [[nodiscard]] std::size_t Count() const noexcept
            {
                return Items.size();
            }

            std::unordered_map<std::uint32_t, T> Items;
        };

        template <typename T>
        [[nodiscard]] ComponentPool<T>* FindPool() noexcept
        {
            const auto iterator = Pools.find(std::type_index(typeid(T)));
            return iterator == Pools.end() ? nullptr : static_cast<ComponentPool<T>*>(iterator->second.get());
        }

        template <typename T>
        [[nodiscard]] const ComponentPool<T>* FindPool() const noexcept
        {
            const auto iterator = Pools.find(std::type_index(typeid(T)));
            return iterator == Pools.end() ? nullptr : static_cast<const ComponentPool<T>*>(iterator->second.get());
        }

        template <typename T>
        ComponentPool<T>& GetOrCreatePool()
        {
            const std::type_index type(typeid(T));
            auto iterator = Pools.find(type);
            if (iterator == Pools.end())
            {
                auto pool = std::make_unique<ComponentPool<T>>();
                ComponentPool<T>* result = pool.get();
                Pools.emplace(type, std::move(pool));
                return *result;
            }
            return *static_cast<ComponentPool<T>*>(iterator->second.get());
        }

        [[nodiscard]] Entity AllocateEntity();

        std::vector<Slot> Slots;
        std::vector<std::uint32_t> FreeIndices;
        std::unordered_map<std::type_index, std::unique_ptr<IComponentPool>> Pools;
        std::size_t AliveCount = 0;
    };
}
