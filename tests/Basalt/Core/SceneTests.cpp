#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include <doctest/doctest.h>

#include <Basalt/Core/Scene.h>

#include <cstddef>
#include <string>

namespace
{
    struct Velocity final
    {
        float X = 0.0F;
    };
}

TEST_CASE("A scene creates entities with a transform and optional name")
{
    Basalt::Scene scene;
    const Basalt::Entity actor = scene.CreateEntity("Test actor");

    REQUIRE(scene.IsAlive(actor));
    CHECK(scene.EntityCount() == 1U);
    REQUIRE(scene.GetComponent<Basalt::Transform>(actor) != nullptr);
    CHECK(scene.GetComponent<Basalt::Transform>(actor)->Position == glm::vec3(0.0F));
    REQUIRE(scene.GetComponent<Basalt::Name>(actor) != nullptr);
    CHECK(scene.GetComponent<Basalt::Name>(actor)->Value == "Test actor");

    const Basalt::Entity unnamed = scene.CreateEntity();
    CHECK(scene.IsAlive(unnamed));
    CHECK_FALSE(scene.HasComponent<Basalt::Name>(unnamed));
}

TEST_CASE("Transform data can be authored through the component API")
{
    Basalt::Scene scene;
    const Basalt::Entity actor = scene.CreateEntity();
    Basalt::Transform* transform = scene.GetComponent<Basalt::Transform>(actor);
    REQUIRE(transform != nullptr);

    transform->Position = glm::vec3(2.0F, 3.0F, 4.0F);
    transform->Scale = glm::vec3(2.0F);
    CHECK(transform->Position == glm::vec3(2.0F, 3.0F, 4.0F));
    CHECK(transform->Scale == glm::vec3(2.0F));
}

TEST_CASE("Entity destruction invalidates stale handles and permits safe slot reuse")
{
    Basalt::Scene scene;
    const Basalt::Entity oldEntity = scene.CreateEntity();
    REQUIRE(scene.DestroyEntity(oldEntity));
    CHECK_FALSE(scene.IsAlive(oldEntity));
    CHECK_FALSE(scene.DestroyEntity(oldEntity));
    CHECK(scene.EntityCount() == 0U);

    const Basalt::Entity newEntity = scene.CreateEntity();
    CHECK(newEntity.Index == oldEntity.Index);
    CHECK(newEntity.Generation != oldEntity.Generation);
    CHECK_FALSE(scene.IsAlive(oldEntity));
    CHECK(scene.IsAlive(newEntity));
}

TEST_CASE("Destroying an entity removes every component")
{
    Basalt::Scene scene;
    const Basalt::Entity entity = scene.CreateEntity("Moving actor");
    scene.AddComponent<Velocity>(entity, Velocity{5.0F});
    REQUIRE(scene.ComponentCount<Velocity>() == 1U);

    CHECK(scene.DestroyEntity(entity));
    CHECK(scene.ComponentCount<Velocity>() == 0U);
    CHECK(scene.ComponentCount<Basalt::Transform>() == 0U);
    CHECK(scene.ComponentCount<Basalt::Name>() == 0U);
    CHECK(scene.GetComponent<Velocity>(entity) == nullptr);
}

TEST_CASE("Components can be added, queried, iterated, and removed")
{
    Basalt::Scene scene;
    const Basalt::Entity first = scene.CreateEntity();
    const Basalt::Entity second = scene.CreateEntity();
    scene.AddComponent<Velocity>(first, Velocity{1.5F});
    scene.AddComponent<Velocity>(second, Velocity{2.5F});

    CHECK(scene.HasComponent<Velocity>(first));
    REQUIRE(scene.GetComponent<Velocity>(first) != nullptr);
    CHECK(scene.GetComponent<Velocity>(first)->X == doctest::Approx(1.5F));
    CHECK(scene.ComponentCount<Velocity>() == 2U);

    std::size_t visited = 0U;
    float totalVelocity = 0.0F;
    scene.ForEach<Velocity>([&](Basalt::Entity entity, Velocity& velocity)
    {
        CHECK(scene.IsAlive(entity));
        ++visited;
        totalVelocity += velocity.X;
    });
    CHECK(visited == 2U);
    CHECK(totalVelocity == doctest::Approx(4.0F));

    CHECK(scene.RemoveComponent<Velocity>(first));
    CHECK_FALSE(scene.RemoveComponent<Velocity>(first));
    CHECK_FALSE(scene.HasComponent<Velocity>(first));
    CHECK(scene.ComponentCount<Velocity>() == 1U);
}

TEST_CASE("Duplicate components and stale entity writes are rejected")
{
    Basalt::Scene scene;
    const Basalt::Entity entity = scene.CreateEntity();
    scene.AddComponent<Velocity>(entity, Velocity{1.0F});
    CHECK_THROWS_AS(scene.AddComponent<Velocity>(entity, Velocity{2.0F}), std::logic_error);

    REQUIRE(scene.DestroyEntity(entity));
    CHECK_THROWS_AS(scene.AddComponent<Velocity>(entity, Velocity{3.0F}), std::invalid_argument);
    CHECK(scene.GetComponent<Velocity>(entity) == nullptr);
}

TEST_CASE("Empty component iteration is safe")
{
    Basalt::Scene scene;
    std::size_t visited = 0U;
    scene.ForEach<Velocity>([&](Basalt::Entity, Velocity&) { ++visited; });
    CHECK(visited == 0U);
}
