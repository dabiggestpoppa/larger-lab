import sys; sys.path.insert(0, 'engines')
import inspect, symmetry_trap as st
src = inspect.getsource(st.SymmetryTrapEngine.__init__)
print(src[:3000])
