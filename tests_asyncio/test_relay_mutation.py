import pytest
from graphql.execution.executors.asyncio import AsyncioExecutor

from graphene.types import ID, Field, ObjectType, Schema
from graphene.types.scalars import String
from graphene.relay.mutation import ClientIDMutation


class SharedFields(object):
    shared = String()


class MyNode(ObjectType):
    # class Meta:
    #     interfaces = (Node, )
    id = ID()
    name = String()


class SaySomethingAsync(ClientIDMutation):
    class Input:
        what = String()

    phrase = String()

    @staticmethod
    async def mutate_and_get_payload(self, info, what, client_mutation_id=None):
        return SaySomethingAsync(phrase=str(what))


# MyEdge = MyNode.Connection.Edge
class MyEdge(ObjectType):
    node = Field(MyNode)
    cursor = String()


class OtherMutation(ClientIDMutation):
    class Input(SharedFields):
        additional_field = String()

    name = String()
    my_node_edge = Field(MyEdge)

    @staticmethod
    def mutate_and_get_payload(
        self, info, shared="", additional_field="", client_mutation_id=None
    ):
        edge_type = MyEdge
        return OtherMutation(
            name=shared + additional_field,
            my_node_edge=edge_type(cursor="1", node=MyNode(name="name")),
        )


class RootQuery(ObjectType):
    something = String()


class Mutation(ObjectType):
    say_promise = SaySomethingAsync.Field()
    other = OtherMutation.Field()


schema = Schema(query=RootQuery, mutation=Mutation)


@pytest.mark.asyncio
async def test_node_query_promise():
    executed = await schema.execute(
        'mutation a { sayPromise(input: {what:"hello", clientMutationId:"1"}) { phrase } }',
        executor=AsyncioExecutor(),
        return_promise=True,
    )
    assert not executed.errors
    assert executed.data == {"sayPromise": {"phrase": "hello"}}


@pytest.mark.asyncio
async def test_edge_query():
    executed = await schema.execute(
        'mutation a { other(input: {clientMutationId:"1"}) { clientMutationId, myNodeEdge { cursor node { name }} } }',
        executor=AsyncioExecutor(),
        return_promise=True,
    )
    assert not executed.errors
    assert dict(executed.data) == {
        "other": {
            "clientMutationId": "1",
            "myNodeEdge": {"cursor": "1", "node": {"name": "name"}},
        }
    }
