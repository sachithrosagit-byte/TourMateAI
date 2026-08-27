from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app.models import Hotel
from app.extensions import db
from app.services.translation_service import translate_to_sinhala, translate_to_italian

hotels_bp = Blueprint("hotels", __name__)

@hotels_bp.route("/hotels", methods=["GET"])
def get_hotels():
    """Get hotels with optional filtering."""
    query = Hotel.query

    budget_tier = request.args.get("budget_tier")
    if budget_tier:
        query = query.filter(Hotel.budget_tier == budget_tier.lower())

    location = request.args.get("location")
    if location:
        query = query.filter(Hotel.location.ilike(f"%{location}%"))

    search = request.args.get("search")
    if search:
        query = query.filter(
            or_(
                Hotel.name.ilike(f"%{search}%"),
                Hotel.description.ilike(f"%{search}%"),
            )
        )

    # Optional: order by rating
    sort_by = request.args.get("sort_by")
    if sort_by == "rating":
        query = query.order_by(Hotel.avg_rating.desc())
    else:
        query = query.order_by(Hotel.id)

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    lang = request.args.get("lang")

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    hotels = pagination.items

    serialized_hotels = []
    for hotel in hotels:
        h_dict = hotel.to_dict()
        if lang == 'si':
            h_dict["name"] = translate_to_sinhala(h_dict["name"])
            if h_dict["description"]:
                h_dict["description"] = translate_to_sinhala(h_dict["description"])
        elif lang == 'it':
            h_dict["name"] = translate_to_italian(h_dict["name"])
            if h_dict["description"]:
                h_dict["description"] = translate_to_italian(h_dict["description"])
        serialized_hotels.append(h_dict)

    return jsonify(
        {
            "hotels": serialized_hotels,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
        }
    )

@hotels_bp.route("/hotels/<int:hotel_id>", methods=["GET"])
def get_hotel(hotel_id):
    """Get details for a specific hotel."""
    lang = request.args.get("lang")
    hotel = Hotel.query.get_or_404(hotel_id)
    
    h_dict = hotel.to_dict()
    if lang == 'si':
        h_dict["name"] = translate_to_sinhala(h_dict["name"])
        if h_dict["description"]:
            h_dict["description"] = translate_to_sinhala(h_dict["description"])
    elif lang == 'it':
        h_dict["name"] = translate_to_italian(h_dict["name"])
        if h_dict["description"]:
            h_dict["description"] = translate_to_italian(h_dict["description"])
            
    return jsonify({"hotel": h_dict})
