
from app import create_app, db
from app.models import Laundry, LaundryStatusHistory

def update_status():
    app = create_app()
    with app.app_context():
        # Update Laundry table
        laundries = Laundry.query.filter_by(status='Picked Up').all()
        for laundry in laundries:
            laundry.status = 'Ready for Pickup'
        db.session.commit()

        # Update LaundryStatusHistory table
        histories = LaundryStatusHistory.query.filter_by(new_status='Picked Up').all()
        for history in histories:
            history.new_status = 'Ready for Pickup'
        db.session.commit()

if __name__ == '__main__':
    update_status()
    print('All "Picked Up" statuses updated to "Ready for Pickup".')
