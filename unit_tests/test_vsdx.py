import pytest
from vsdx import VisioFile
from datetime import datetime
import os

import xml.etree.ElementTree as ET

our_dir = os.path.dirname(os.path.realpath(__file__))


def test_file_closure():
    print(our_dir)
    filename = os.path.join(our_dir, 'test1.vsdx')
    directory = os.path.splitext(filename)[0]
    with VisioFile(filename):
        # confirm directory exists
        assert os.path.exists(directory)
    # confirm directory is gone
    assert not os.path.exists(directory)


@pytest.mark.parametrize("filename, page_name", [("test1.vsdx", "Page-1"), ("test2.vsdx", "Page-1")])
def test_get_page(filename: str, page_name: str):
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        # confirm page name as expected
        assert page.name == page_name


@pytest.mark.parametrize("filename, count", [("test1.vsdx", 1), ("test2.vsdx", 1)])
def test_get_page_shapes(filename: str, count: int):
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        print(f"shape count={len(page.shapes)}")
        assert len(page.shapes) == count


@pytest.mark.parametrize("filename, count", [("test1.vsdx", 4), ("test2.vsdx", 6)])
def test_get_page_sub_shapes(filename: str, count: int):
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shapes = page.shapes[0].sub_shapes()
        print(f"shape count={len(shapes)}")
        assert len(shapes) == count


@pytest.mark.parametrize("filename, expected_locations",
                         [("test1.vsdx", "1.33,10.66 4.13,10.66 6.94,10.66 2.33,9.02 "),
                          ("test2.vsdx", "2.33,8.72 1.33,10.66 4.13,10.66 5.91,8.72 1.61,8.58 3.25,8.65 ")])
def test_shape_locations(filename: str, expected_locations: str):
    print("=== list_shape_locations ===")
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shapes = page.shapes[0].sub_shapes()
        locations = ""
        for s in shapes:  # type: VisioFile.Shape
            locations += f"{s.x:.2f},{s.y:.2f} "
        print(f"Expected:{expected_locations}")
        print(f"  Actual:{locations}")
    assert locations == expected_locations


@pytest.mark.parametrize("filename, shape_id", [("test1.vsdx", "6"), ("test2.vsdx", "6")])
def test_get_shape_with_text(filename: str, shape_id: str):
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shape = page.shapes[0].find_shape_by_text('{{date}}')  # type: VisioFile.Shape
        assert shape.ID == shape_id


@pytest.mark.parametrize("filename", ["test1.vsdx", "test2.vsdx", "test3_house.vsdx"])
def test_apply_context(filename: str):
    date_str = str(datetime.today().date())
    context = {'scenario': 'test',
               'date': date_str}
    out_file = 'out' + os.sep + filename[:-5] + '_VISfilter_applied.vsdx'
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        original_shape = page.shapes[0].find_shape_by_text('{{date}}')  # type: VisioFile.Shape
        assert original_shape.ID
        page.apply_text_context(context)
        vis.save_vsdx(out_file)

    # open and find date_str
    with VisioFile(out_file) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        updated_shape = page.shapes[0].find_shape_by_text(date_str)  # type: VisioFile.Shape
        assert updated_shape.ID == original_shape.ID


@pytest.mark.parametrize("filename", ["test1.vsdx", "test2.vsdx", "test3_house.vsdx"])
def test_find_replace(filename: str):
    old = 'Shape'
    new = 'Figure'
    out_file = 'out' + os.sep + filename[:-5] + '_VISfind_replace_applied.vsdx'
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        original_shapes = page.find_shapes_by_text(old)  # type: VisioFile.Shape
        shape_ids = [s.ID for s in original_shapes]
        page.find_replace(old, new)
        vis.save_vsdx(out_file)

    # open and find date_str
    with VisioFile(out_file) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        # test that each shape if has 'new' str in text
        for shape_id in shape_ids:
            shape = page.find_shape_by_id(shape_id)
            assert new in shape.text


@pytest.mark.parametrize("filename", ["test2.vsdx", "test3_house.vsdx"])
def test_remove_shape(filename: str):
    out_file = 'out' + os.sep + filename[:-5] + '_shape_removed.vsdx'
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        shapes = vis.page_objects[0].shapes
        # get shape to remove
        s = shapes[0].find_shape_by_text('Shape to remove')  # type: VisioFile.Shape
        assert s  # check shape found
        s.remove()
        vis.save_vsdx(out_file)

    with VisioFile(out_file) as vis:
        shapes = vis.page_objects[0].shapes
        # get shape that should have been removed
        s = shapes[0].find_shape_by_text('Shape to remove')  # type: VisioFile.Shape
        assert s is None  # check shape not found


@pytest.mark.parametrize(("filename", "shape_names", "shape_locations"),
                         [("test1.vsdx", {"Shape to remove"}, {(1.0, 1.0)})])
def test_set_shape_location(filename: str, shape_names: set, shape_locations: set):
    out_file = 'out' + os.sep + filename[:-5] + '_test_set_shape_location.vsdx'
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        shapes = vis.page_objects[0].shapes
        # move shapes in list
        for (shape_name, x_y) in zip(shape_names, shape_locations):
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x
            assert s.y
            print(f"Moving shape '{shape_name}' from {s.x}, {s.y} to {x_y}")
            s.x = x_y[0]
            s.y = x_y[1]
        vis.save_vsdx(out_file)

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        shapes = vis.page_objects[0].shapes
        # get each shape that should have been moved
        for (shape_name, x_y) in zip(shape_names, shape_locations):
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x == x_y[0]
            assert s.y == x_y[1]


@pytest.mark.parametrize(("filename", "shape_names", "shape_x_y_deltas"),
                         [("test1.vsdx", {"Shape to remove"}, {(1.0, 1.0)})])
def test_move_shape(filename: str, shape_names: set, shape_x_y_deltas: set):
    out_file = 'out' + os.sep + filename[:-5] + '_test_move_shape.vsdx'
    expected_shape_locations = dict()

    with VisioFile(os.path.join(our_dir, filename)) as vis:
        shapes = vis.page_objects[0].shapes
        # move shapes in list
        for (shape_name, x_y) in zip(shape_names, shape_x_y_deltas):
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x
            assert s.y
            expected_shape_locations[shape_name] = (s.x + x_y[0], s.y + x_y[1])
            s.move(x_y[0], x_y[1])

        vis.save_vsdx(out_file)
    print(f"expected_shape_locations={expected_shape_locations}")

    # re-open saved file and check it is changed as expected
    with VisioFile(out_file) as vis:
        shapes = vis.page_objects[0].shapes
        # get each shape that should have been moved
        for shape_name in shape_names:
            s = shapes[0].find_shape_by_text(shape_name)  # type: VisioFile.Shape
            assert s  # check shape found
            assert s.x == expected_shape_locations[shape_name][0]
            assert s.y == expected_shape_locations[shape_name][1]


@pytest.mark.parametrize(("filename"),
                         [('test4_lines.vsdx')])
def test_master_inheritance(filename: str):
    with VisioFile(os.path.join(our_dir, filename)) as vis:
        page = vis.get_page(0)  # type: VisioFile.Page
        shape_a = page.find_shapes_by_text('Shape A')  # type: VisioFile.Shape
        shape_b = page.find_shapes_by_text('Shape B')  # type: VisioFile.Shape
        assert shape_a
        assert shape_b
