import java.util.*;

public class Day09_DatabaseAlgebra {
    record Student(int id, String name) {}
    record Enrollment(int studentId, String course, int marks) {}
    record Result(String name, String course) {}
    public static void main(String[] args) {
        List<Student> students = List.of(new Student(1, "Asha"), new Student(2, "Ravi"));
        List<Enrollment> enrollments = List.of(
            new Enrollment(1, "DBMS", 82), new Enrollment(2, "OS", 74));
        List<Result> joined = new ArrayList<>();
        for (Enrollment e : enrollments) if (e.marks() >= 80)
            for (Student s : students) if (s.id() == e.studentId())
                joined.add(new Result(s.name(), e.course()));
        if (!joined.equals(List.of(new Result("Asha", "DBMS")))) throw new AssertionError(joined);
        List<String> projected = joined.stream().map(Result::name).toList();
        System.out.println("selection + join: " + joined + " | projection: " + projected);
    }
}
