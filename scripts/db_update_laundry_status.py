from app import create_app, db
from app.models import Laundry


def update_laundry_status():
    app = create_app()
    with app.app_context():
        updated = Laundry.query.filter_by(status="Picked Up").update(
            {Laundry.status: "Ready for Pickup"}
        )
        db.session.commit()
        print(
            f"Updated {updated} Laundry records from 'Picked Up' to 'Ready for Pickup'."
        )


if __name__ == "__main__":
    update_laundry_status()
