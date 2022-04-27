from __future__ import annotations

import json
from http import HTTPStatus

import edgedb
from flask import Blueprint, request

movie = Blueprint("movie", __name__)
client = edgedb.create_client()

################################
# Get actors
################################


@movie.route("/movies", methods=["GET"])
def get_movies() -> tuple[dict, int]:
    movies = client.query_json(
        """
        SELECT Movie {name, year, actors:{name, age}}
    """
    )
    response_payload = {"result": json.loads(movies)}
    return response_payload, HTTPStatus.OK


################################
# Create actor
################################


@movie.route("/movies", methods=["POST"])
def post_movie() -> tuple[dict, int]:
    incoming_payload = request.json

    # Exception handling.
    if not incoming_payload:
        return {"error": "Bad request"}, HTTPStatus.BAD_REQUEST

    if not (name := incoming_payload.get("name")):
        return {"error": "Field 'name' is required."}, HTTPStatus.BAD_REQUEST

    if len(name) > 50:
        return {
            "error": "Field 'name' cannot be longer than 50 characters."
        }, HTTPStatus.BAD_REQUEST

    if year := incoming_payload.get("year"):
        if year < 1850:
            return {
                "error": "Field 'year' cannot be less than 1850."
            }, HTTPStatus.BAD_REQUEST

    actor_names = incoming_payload.get("actor_names")

    # Save data to db.
    movie = client.query_single_json(
        """
        WITH name:=<str>$name, year:=<optional int16>$year,
            actor_names:=<optional array<str>>$actor_names
            SELECT (
                INSERT Movie {
                name:=name, year:=year,
                actors:=(
                    SELECT DETACHED Actor FILTER
                    .name in array_unpack(actor_names))
                }
            ){name, year, actors: {name, age, height}};
        """,
        name=name,
        year=year,
        actor_names=actor_names,
    )
    response_payload = {"result": json.loads(movie)}
    return response_payload, HTTPStatus.CREATED


################################
# Update actors
################################


@movie.route("/movies", methods=["PUT"])
def put_movies() -> tuple[dict, int]:
    incoming_payload = request.json
    filter_name = request.args.get("filter_name")

    # Exception handling.
    if not incoming_payload:
        return {"error": "Bad request"}, HTTPStatus.BAD_REQUEST

    if not filter_name:
        return {
            "error": "Query parameter 'filter_name' must be provided",
        }, HTTPStatus.BAD_REQUEST

    if not (name := incoming_payload.get("name")):
        return {"error": "Field 'name' is required."}, HTTPStatus.BAD_REQUEST

    if len(name) > 50:
        return {
            "error": "Field 'name' cannot be longer than 50 characters."
        }, HTTPStatus.BAD_REQUEST

    if year := incoming_payload.get("year"):
        if year < 1850:
            return {
                "error": "Field 'year' cannot be less than 1850."
            }, HTTPStatus.BAD_REQUEST

    actor_names = incoming_payload.get("actor_names", [])
    movies = client.query_json(
        """
        WITH filter_name:=<str>$filter_name, name:=<str>$name,
            year:=<optional int16>$year,
            actor_names:=<optional array<str>>$actor_names

            SELECT (
                UPDATE Movie FILTER .name=filter_name
                SET {
                    name:=name, year:=year ?? .year,
                    actors:=(
                        SELECT DETACHED Actor FILTER .name
                        IN array_unpack(actor_names)
                    ) ?? .actors
                }){name, year, actors : {name, age, height}};""",
        filter_name=filter_name,
        name=name,
        year=year,
        actor_names=actor_names,
    )
    response_payload = {"result": json.loads(movies)}
    return response_payload, HTTPStatus.OK


################################
# Delete actors
################################


@movie.route("/movies", methods=["DELETE"])
def delete_movies() -> tuple[dict, int]:
    # Exception handling.
    if not (filter_name := request.args.get("filter_name")):
        return {
            "error": "Query parameter 'filter_name' must be provided",
        }, HTTPStatus.BAD_REQUEST

    movies = client.query_json(
        "SELECT (DELETE Movie FILTER .name=<str>$filter_name){name}",
        filter_name=filter_name,
    )
    response_payload = {"result": json.loads(movies)}
    return response_payload, HTTPStatus.OK