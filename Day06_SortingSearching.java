import java.util.*;

public class Day06_SortingSearching {
    static int[] mergeSort(int[] a) {
        if (a.length <= 1) return a.clone();
        int mid = a.length / 2;
        int[] left = mergeSort(Arrays.copyOfRange(a, 0, mid));
        int[] right = mergeSort(Arrays.copyOfRange(a, mid, a.length));
        int[] out = new int[a.length]; int i = 0, j = 0, k = 0;
        while (i < left.length && j < right.length)
            out[k++] = left[i] <= right[j] ? left[i++] : right[j++];
        while (i < left.length) out[k++] = left[i++];
        while (j < right.length) out[k++] = right[j++];
        return out;
    }
    static int binarySearch(int[] a, int target) {
        int low = 0, high = a.length - 1;
        while (low <= high) {
            int mid = low + (high - low) / 2;
            if (a[mid] == target) return mid;
            if (a[mid] < target) low = mid + 1; else high = mid - 1;
        }
        return -1;
    }
    public static void main(String[] args) {
        int[] sorted = mergeSort(new int[]{8, 3, 6, 1, 5});
        if (!Arrays.equals(sorted, new int[]{1, 3, 5, 6, 8}) || binarySearch(sorted, 6) != 3)
            throw new AssertionError("sort/search");
        System.out.println("sorted: " + Arrays.toString(sorted) + " | index of 6: 3");
    }
}
