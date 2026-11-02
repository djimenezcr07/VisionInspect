#include "inspection.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cstring>
namespace py=pybind11;
PYBIND11_MODULE(vision_engine,m) {
 m.doc()="Motor C++17/OpenCV de demostración";m.attr("__version__")="1.0.0";
 m.def("inspect",[](py::array_t<unsigned char,py::array::c_style|py::array::forcecast> data,int foreground,int darkness,int min_area,int min_radius){
  auto b=data.request(); if(b.ndim!=3||b.shape[2]!=3) throw std::invalid_argument("La imagen debe tener tres canales BGR.");
  if(b.shape[0]>4096||b.shape[1]>4096||b.shape[0]<64||b.shape[1]<64) throw std::invalid_argument("Dimensiones fuera del rango admitido.");
  cv::Mat image((int)b.shape[0],(int)b.shape[1],CV_8UC3,b.ptr); auto r=vision::inspect(image,{foreground,darkness,min_area,min_radius});
  py::list boxes; for(const auto &a:r.regions){py::dict x;x["x"]=a.x;x["y"]=a.y;x["ancho"]=a.width;x["alto"]=a.height;x["area_px2"]=a.area;boxes.append(x);}
  py::dict result;result["pieza_detectada"]=r.found;result["centro_x"]=r.found?py::cast(r.cx):py::none();result["centro_y"]=r.found?py::cast(r.cy):py::none();result["radio_px"]=r.found?py::cast(r.radius):py::none();result["regiones"]=boxes;result["advertencia"]=r.warning;
  py::array_t<unsigned char> output({b.shape[0],b.shape[1],py::ssize_t(3)}); std::memcpy(output.mutable_data(),r.annotated.data,r.annotated.total()*3);return py::make_tuple(result,output);
 },py::arg("image"),py::arg("foreground")=90,py::arg("darkness")=75,py::arg("min_area")=35,py::arg("min_radius")=40);
}
