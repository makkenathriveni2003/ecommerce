from sqlalchemy import event, select
from sqlalchemy.orm import selectinload, joinedload
from auth import create_access_token
from db_session import SessionLocal, engine
from models import Order, OrderItem
from main import get_sqlalchemy_orders_optimized

def test_sqlalchemy_n_plus_one_avoidance():
    """Verify that SQLAlchemy eager loading executes a constant number of queries (2 queries) regardless of N orders."""
    queries_run = []

    def count_queries(conn, cursor, statement, parameters, context, executemany):
        queries_run.append(statement)

    event.listen(engine, "before_cursor_execute", count_queries)

    try:
        queries_run.clear()
        db = SessionLocal()
        stmt = (
            select(Order)
            .options(selectinload(Order.items).joinedload(OrderItem.product))
            .order_by(Order.id.desc())
            .limit(10)
        )
        orders = db.execute(stmt).scalars().all()
        # Accessing all order items and their products
        results = [o.to_dict() for o in orders]
        db.close()

        # Check total query count
        query_count = len(queries_run)
        assert query_count <= 2, f"Expected <= 2 queries, got {query_count} queries (N+1 query detected!)"
    finally:
        event.remove(engine, "before_cursor_execute", count_queries)


def test_optimized_orders_api_endpoint(client):
    """Test /orders/optimized endpoint returns valid orders and serialized items."""
    token = create_access_token("shopper@example.com")
    response = client.get(
        "/orders/optimized",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    orders = response.json()
    assert isinstance(orders, list)
    if len(orders) > 0:
        assert "items" in orders[0]
        assert "total" in orders[0]
