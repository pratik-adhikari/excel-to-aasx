from excel_to_aasx.package import aasx_package_path, collect_missing_supplementary_files


def test_collect_missing_supplementary_files_ignores_external_urls() -> None:
    payload = {
        "submodels": [
            {
                "modelType": "Submodel",
                "submodelElements": [
                    {
                        "idShort": "ExternalImage",
                        "modelType": "File",
                        "value": "https://example.com/image.webp",
                        "contentType": "image/webp",
                    },
                    {
                        "idShort": "LocalDocument",
                        "modelType": "File",
                        "value": "manual.pdf",
                        "contentType": "application/pdf",
                    },
                ],
            }
        ]
    }

    assert collect_missing_supplementary_files(payload) == [
        {
            "path": "/aasx/files/manual.pdf",
            "originalPath": "manual.pdf",
            "contentType": "application/pdf",
            "reason": "File reference is local/relative but no source file is available; placeholder added to AASX.",
        }
    ]
    local = payload["submodels"][0]["submodelElements"][1]
    assert local["value"] == "/aasx/files/manual.pdf"


def test_aasx_package_path_avoids_double_encoding_and_trailing_dot() -> None:
    assert (
        aasx_package_path("Maintenance%20flowchart%20not%20available.")
        == "/aasx/files/Maintenance%20flowchart%20not%20available"
    )
